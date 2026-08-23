import java.util.concurrent.locks.ReentrantLock;

public final class ConcurrentTransfer {
    private ConcurrentTransfer() {}

    public static final class Account {
        public final long id;
        private long balance;
        final ReentrantLock lock = new ReentrantLock();

        public Account(long id, long balance) {
            if (balance < 0) {
                throw new IllegalArgumentException("balance must be non-negative");
            }
            this.id = id;
            this.balance = balance;
        }

        public long balance() {
            lock.lock();
            try {
                return balance;
            } finally {
                lock.unlock();
            }
        }
    }

    public static boolean transfer(Account from, Account to, long amount) {
        if (from == null || to == null) {
            throw new NullPointerException("accounts");
        }
        if (amount <= 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
        if (from == to) {
            return true;
        }
        if (from.id == to.id) {
            throw new IllegalArgumentException("distinct accounts must have unique ids");
        }

        Account first = from.id < to.id ? from : to;
        Account second = from.id < to.id ? to : from;

        first.lock.lock();
        try {
            second.lock.lock();
            try {
                if (from.balance < amount) {
                    return false;
                }
                long newFrom = from.balance - amount;
                long newTo = Math.addExact(to.balance, amount);
                from.balance = newFrom;
                to.balance = newTo;
                return true;
            } finally {
                second.lock.unlock();
            }
        } finally {
            first.lock.unlock();
        }
    }
}
