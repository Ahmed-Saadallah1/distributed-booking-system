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
import time

# ─────────────────────────────────────────────
# GLOBAL SHARED STATE (the central server)
# ─────────────────────────────────────────────
INITIAL_SEATS        = 300
global_available     = INITIAL_SEATS
global_booked        = 0
global_cancelled     = 0
audit_log            = []

# Lock — only one counter can sync at a time
sync_lock = threading.Lock()


# ─────────────────────────────────────────────
# SYNC FUNCTION — called by each counter at end of round
# ─────────────────────────────────────────────
def sync_memory(counter_id, round_id, local_queue):
    global global_available, global_booked, global_cancelled

    with sync_lock:
        print(f"\n[SYNC - S] Counter {counter_id} syncing Round {round_id}...")

        applied_bookings    = 0
        applied_cancels     = 0
        rejected_bookings   = 0

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
                    global_available  += 1
                    global_booked     -= 1
                    global_cancelled  += 1
                    applied_cancels   += 1

        print(f"[SYNC - S] Applied bookings: {applied_bookings}")
        print(f"[SYNC - S] Applied cancellations: {applied_cancels}")
        print(f"[SYNC - S] Rejected bookings (overbook protection): {rejected_bookings}")
        print(f"[SYNC - S] Global seats after sync: {global_available}")

        # Store audit record
        audit_log.append({
            "counter":   counter_id,
            "round":     round_id,
            "booked":    applied_bookings,
            "cancelled": applied_cancels,
            "rejected":  rejected_bookings,
            "seats_after": global_available
        })


# ─────────────────────────────────────────────
# COUNTER FUNCTION — simulates one ticket counter
# ─────────────────────────────────────────────
def run_counter(counter_id, num_rounds):
    for round_id in range(1, num_rounds + 1):

        # ── Prepare local operations (randomly generate book/cancel requests)
        print(f"\nCounter {counter_id} preparing Round {round_id} local operations...")
        time.sleep(random.uniform(0.01, 0.05))  # simulate processing time

        num_books   = random.randint(10, 60)
        num_cancels = random.randint(1, 10)
        local_queue = ["book"] * num_books + ["cancel"] * num_cancels
        random.shuffle(local_queue)

        # ── Stale read — counter reads global seats BEFORE syncing
        # This value may be outdated because other counters haven't synced yet
        stale_read = global_available
        print(f"-> Counter {counter_id}, Round {round_id}, reads global seats: {stale_read} (may be stale)")

        # ── Sync with global server at end of round
        sync_memory(counter_id, round_id, local_queue)


# ─────────────────────────────────────────────
# MAIN — spin up 4 counters as threads
# ─────────────────────────────────────────────
def main():
    NUM_COUNTERS = 4
    NUM_ROUNDS   = 5

    print("=" * 50)
    print("  DISTRIBUTED THEATER BOOKING SYSTEM")
    print(f"  Initial seats: {INITIAL_SEATS}")
    print(f"  Counters: {NUM_COUNTERS} | Rounds: {NUM_ROUNDS}")
    print("=" * 50)

    # Create one thread per counter
    threads = []
    for i in range(1, NUM_COUNTERS + 1):
        t = threading.Thread(target=run_counter, args=(i, NUM_ROUNDS))
        threads.append(t)

    # Start all counters simultaneously
    for t in threads:
        t.start()

    # Wait for all counters to finish
    for t in threads:
        t.join()

    # ── Final Report
    print("\n\n" + "=" * 46)
    print("================ FINAL REPORT ================")
    print("=" * 46)
    print(f"Initial seats:                    {INITIAL_SEATS}")
    print(f"Total booked seats (applied):     {global_booked + global_cancelled}")
    print(f"Total cancelled seats (applied):  {global_cancelled}")
    print(f"Final global available seats:     {global_available}")

    expected = INITIAL_SEATS - global_booked
    print(f"Expected available seats:         {expected}")

    invariant_check = "PASS" if global_available == expected else "FAIL"
    print(f"Invariant check:                  {invariant_check}")
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
