"""
Assignment 2: Distributed Theater Booking System
Course: Distributed Systems and Web Services - Spring 2026

Simulates weak consistency in a distributed system where:
- 4 ticket counters work in parallel
- Each counter handles requests locally per round (stale reads)
- At end of each round, counters sync with global server using a lock
- Overbooking protection is applied during synchronization
"""

import threading
import random

# ─────────────────────────────────────────────
# GLOBAL SHARED STATE (the central server)
# ─────────────────────────────────────────────
INITIAL_SEATS    = 300
global_available = INITIAL_SEATS
global_booked    = 0
global_cancelled = 0
audit_log        = []

# sync_lock  — only one counter can update global state at a time
# print_lock — prevents print lines from mixing between threads
sync_lock  = threading.Lock()
print_lock = threading.Lock()

def safe_print(msg):
    with print_lock:
        print(msg)


# ─────────────────────────────────────────────
# SYNC FUNCTION — called by each counter at end of round
# ─────────────────────────────────────────────
def sync_memory(counter_id, round_id, local_queue):
    global global_available, global_booked, global_cancelled

    with sync_lock:
        safe_print(f"[SYNC - S] Counter {counter_id} syncing Round {round_id}...")

        applied_bookings  = 0
        applied_cancels   = 0
        rejected_bookings = 0

        for operation in local_queue:
            if operation == "book":
                if global_available > 0:
                    global_available -= 1
                    global_booked    += 1
                    applied_bookings += 1
                else:
                    rejected_bookings += 1
            elif operation == "cancel":
                if global_booked > 0:
                    global_available += 1
                    global_booked    -= 1
                    global_cancelled += 1
                    applied_cancels  += 1

        safe_print(f"[SYNC - S] Applied bookings: {applied_bookings}")
        safe_print(f"[SYNC - S] Applied cancellations: {applied_cancels}")
        safe_print(f"[SYNC - S] Rejected bookings (overbook protection): {rejected_bookings}")
        safe_print(f"[SYNC - S] Global seats after sync: {global_available}")

        # Store audit record
        audit_log.append({
            "counter":     counter_id,
            "round":       round_id,
            "booked":      applied_bookings,
            "cancelled":   applied_cancels,
            "rejected":    rejected_bookings,
            "seats_after": global_available
        })


# ─────────────────────────────────────────────
# COUNTER FUNCTION — simulates one ticket counter
# ─────────────────────────────────────────────
def run_counter(counter_id, num_rounds, prepare_barrier, read_barrier):
    for round_id in range(1, num_rounds + 1):

        # ── Each counter prepares its local queue independently
        safe_print(f"Counter {counter_id} preparing Round {round_id} local operations...")

        num_books   = random.randint(10, 60)
        num_cancels = random.randint(1, 10)
        local_queue = ["book"] * num_books + ["cancel"] * num_cancels
        random.shuffle(local_queue)

        # ── Wait for ALL counters to finish preparing before anyone reads
        # This is what causes the stale read — all counters read the same
        # global value before any sync has happened this round
        prepare_barrier.wait()

        # ── Stale read — all counters read the same (possibly outdated) value
        stale_read = global_available
        safe_print(f"-> Counter {counter_id}, Round {round_id}, reads global seats: {stale_read} (may be stale)")

        # ── Wait for ALL counters to finish reading before syncing
        read_barrier.wait()

        # ── Sync with global server — one counter at a time (lock enforces this)
        sync_memory(counter_id, round_id, local_queue)


# ─────────────────────────────────────────────
# MAIN — spin up 4 counters as threads
# ─────────────────────────────────────────────
def main():
    NUM_COUNTERS = 4
    NUM_ROUNDS   = 5

    print("=" * 46)
    print("  DISTRIBUTED THEATER BOOKING SYSTEM")
    print(f"  Initial seats: {INITIAL_SEATS}")
    print(f"  Counters: {NUM_COUNTERS} | Rounds: {NUM_ROUNDS}")
    print("=" * 46)

    # Barriers synchronize all threads at key points each round:
    # prepare_barrier → all counters finish preparing before any reads
    # read_barrier    → all counters finish reading before any syncs
    prepare_barrier = threading.Barrier(NUM_COUNTERS)
    read_barrier    = threading.Barrier(NUM_COUNTERS)

    # Create one thread per counter
    threads = []
    for i in range(1, NUM_COUNTERS + 1):
        t = threading.Thread(
            target=run_counter,
            args=(i, NUM_ROUNDS, prepare_barrier, read_barrier)
        )
        threads.append(t)

    # Start all counters simultaneously
    for t in threads:
        t.start()

    # Wait for all counters to finish all rounds
    for t in threads:
        t.join()

    # ── Final Report
    print("\n================ FINAL REPORT ================")
    print(f"Initial seats: {INITIAL_SEATS}")
    print(f"Total booked seats (applied): {global_booked + global_cancelled}")
    print(f"Total cancelled seats (applied): {global_cancelled}")
    print(f"Final global available seats: {global_available}")
    expected = INITIAL_SEATS - global_booked
    print(f"Expected available seats from invariant: {expected}")
    invariant_check = "PASS" if global_available == expected else "FAIL"
    print(f"Invariant check: {invariant_check}")
    print("=" * 46)

    # ── Audit Log
    print("\n================ AUDIT LOG ===================")
    print(f"{'Counter':<10} {'Round':<8} {'Booked':<10} {'Cancelled':<12} {'Rejected':<10} {'Seats After'}")
    print("-" * 60)
    for entry in audit_log:
        print(f"{entry['counter']:<10} {entry['round']:<8} {entry['booked']:<10} {entry['cancelled']:<12} {entry['rejected']:<10} {entry['seats_after']}")
    print("=" * 46)


if __name__ == "__main__":
    main()
