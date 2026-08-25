"""Cache one club-report page per club per month, for the finished years.

Safe to re-run: anything already cached is skipped, so an interrupted run
resumes where it left off. To refresh a month, delete those files from
data/cache/ and run again.
"""
import os, sys, gzip, queue, threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

THREADS = 8


def cache_path(club_id, program_year, month):
    return os.path.join(C.CACHE, f"{club_id}_{program_year}_{month:02d}.html.gz")


def fetch(club_id, program_year, month, year):
    dest = cache_path(club_id, program_year, month)
    if os.path.exists(dest) and os.path.getsize(dest) > 500:
        return
    page = C.get(C.club_report_url(club_id, program_year, month, year))
    if page is None:
        return
    with gzip.open(dest, "wt", encoding="utf-8") as fh:
        fh.write(page)


def main():
    os.makedirs(C.CACHE, exist_ok=True)
    clubs = C.load_clubs()
    years = C.program_years()
    jobs = [
        (cid, py, m, y)
        for cid, _ in clubs
        for py in years
        for (m, y) in C.months_of(py)
    ]
    print(f"clubs={len(clubs)} years={len(years)} jobs={len(jobs)}", flush=True)

    work = queue.Queue()
    for job in jobs:
        work.put(job)

    done = [0]
    lock = threading.Lock()

    def worker():
        while True:
            try:
                cid, py, m, y = work.get_nowait()
            except queue.Empty:
                return
            fetch(cid, py, m, y)
            with lock:
                done[0] += 1
                if done[0] % 500 == 0:
                    print(f"  {done[0]}/{len(jobs)}", flush=True)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"DONE {done[0]}/{len(jobs)}", flush=True)


if __name__ == "__main__":
    main()
