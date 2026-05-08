# 🎭 Distributed Theater Booking System

A Python simulation of a distributed ticket booking system demonstrating **weak consistency** and **lock-based synchronization**, as used in real-world distributed systems.

---

## 📌 Overview

This project simulates a popular movie night with **300 seats** and **4 ticket counters** working in parallel across **5 rounds**. It demonstrates how distributed systems handle temporary inconsistency and how locks protect shared state during synchronization.

| Property | Value |
|----------|-------|
| 🎟️ Total Seats | 300 |
| 🖥️ Ticket Counters | 4 (parallel threads) |
| 🔄 Rounds | 5 |
| 🔒 Sync Mechanism | Threading Lock |
| 📖 Consistency Model | Weak Consistency |

---

## 🔄 How It Works

```
Round Start:
  All 4 counters prepare local operations (book/cancel) independently
  Each counter reads global seats → may be STALE (weak consistency)

End of Round:
  Each counter acquires the LOCK → syncs with global server
  Overbooking is rejected during sync
  Lock is released → next counter syncs

After All Rounds:
  Final report + audit log printed
  Invariant check: available = initial - booked
```

---

## 🧠 Key Concepts

### 1. Weak Consistency
Counters read the global seat count **before** other counters have synced. This means they may act on **stale (outdated) data**:
```
Counter 2, Round 1, reads global seats: 300 (may be stale)
Counter 3, Round 1, reads global seats: 300 (may be stale)
```
Both think 300 seats are available — but Counter 2 may have already booked some!

### 2. Lock-Based Synchronization
Only **one counter** can update the global state at a time:
```python
with sync_lock:
    # apply local operations to global state
    # reject overbooking if needed
```
This prevents race conditions and data corruption during sync.

### 3. Overbooking Protection
If a counter tries to book more seats than available during sync, the excess requests are **rejected**:
```
[SYNC - S] Rejected bookings (overbook protection): 18
```

---

## 📁 Project Structure

```
distributed-booking-system/
└── booking_system.py    # Main source code
```

---

## ▶️ How to Run

```bash
python booking_system.py
```

No external dependencies — uses Python's built-in `threading` module only.

**Expected output:**
```
Counter 1 preparing Round 1 local operations...
-> Counter 1, Round 1, reads global seats: 300 (may be stale)
[SYNC - S] Counter 1 syncing Round 1...
[SYNC - S] Applied bookings: 45
[SYNC - S] Applied cancellations: 5
[SYNC - S] Rejected bookings (overbook protection): 0
[SYNC - S] Global seats after sync: 255
...
================ FINAL REPORT ================
Invariant check: PASS
```

---

## 🧰 Tech Stack

- **Language:** Python 3
- **Library:** `threading` (built-in)
- **Concepts:** Weak Consistency, Mutual Exclusion, Distributed Synchronization

---

## 💡 Real-World Relevance

This pattern mirrors real distributed databases like **Cassandra** and **DynamoDB** which use eventual/weak consistency for performance, then reconcile state during synchronization windows — exactly what this simulation demonstrates.

---

## 👨‍💻 Author

**Ahmed Saadallah**
GitHub: [@Ahmed-Saadallah1](https://github.com/Ahmed-Saadallah1)
