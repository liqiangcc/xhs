import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class MultiplyThreeAddFiveValidation {
    record Step(int value, String operation) {}

    static List<Step> shortestPath(int target) {
        if (target < 1) return List.of();
        if (target == 1) return List.of(new Step(1, "START"));
        Deque<Integer> queue = new ArrayDeque<>();
        Set<Integer> visited = new HashSet<>();
        Map<Integer, Integer> parent = new HashMap<>();
        Map<Integer, String> operation = new HashMap<>();
        queue.add(1);
        visited.add(1);
        while (!queue.isEmpty()) {
            int current = queue.removeFirst();
            long[] nextValues = {(long) current * 3, (long) current + 5};
            String[] operations = {"*3", "+5"};
            for (int i = 0; i < nextValues.length; i++) {
                long raw = nextValues[i];
                if (raw > target) continue;
                int next = (int) raw;
                if (!visited.add(next)) continue;
                parent.put(next, current);
                operation.put(next, operations[i]);
                if (next == target) return rebuild(target, parent, operation);
                queue.addLast(next);
            }
        }
        return List.of();
    }

    private static List<Step> rebuild(int target, Map<Integer, Integer> parent, Map<Integer, String> operation) {
        List<Step> reversed = new ArrayList<>();
        int current = target;
        while (current != 1) {
            reversed.add(new Step(current, operation.get(current)));
            current = parent.get(current);
        }
        reversed.add(new Step(1, "START"));
        Collections.reverse(reversed);
        return reversed;
    }

    // Independent monotone-DAG oracle: x can only be reached from x-5 or x/3.
    static int oracleMinSteps(int target) {
        if (target < 1) return -1;
        final int inf = 1_000_000;
        int[] dp = new int[target + 1];
        Arrays.fill(dp, inf);
        dp[1] = 0;
        for (int x = 2; x <= target; x++) {
            if (x - 5 >= 1 && dp[x - 5] != inf) dp[x] = Math.min(dp[x], dp[x - 5] + 1);
            if (x % 3 == 0 && x / 3 >= 1 && dp[x / 3] != inf) dp[x] = Math.min(dp[x], dp[x / 3] + 1);
        }
        return dp[target] == inf ? -1 : dp[target];
    }

    static void assertValidPath(int target, List<Step> path) {
        if (path.isEmpty()) throw new AssertionError("expected reachable target " + target);
        if (path.get(0).value() != 1 || !path.get(0).operation().equals("START")) throw new AssertionError("bad start");
        for (int i = 1; i < path.size(); i++) {
            Step prev = path.get(i - 1);
            Step cur = path.get(i);
            int expected = switch (cur.operation()) {
                case "*3" -> prev.value() * 3;
                case "+5" -> prev.value() + 5;
                default -> throw new AssertionError("unknown operation " + cur.operation());
            };
            if (cur.value() != expected) throw new AssertionError("invalid transition " + prev + " -> " + cur);
        }
        if (path.get(path.size() - 1).value() != target) throw new AssertionError("wrong target");
    }

    public static void main(String[] args) {
        List<Step> path = shortestPath(1024);
        assertValidPath(1024, path);
        List<Integer> values = path.stream().map(Step::value).toList();
        List<Integer> expected = List.of(1,3,9,27,32,37,111,333,338,1014,1019,1024);
        if (!values.equals(expected)) throw new AssertionError("unexpected deterministic path: " + values);
        if (path.size() - 1 != 11) throw new AssertionError("expected 11 operations");
        if (oracleMinSteps(1024) != 11) throw new AssertionError("independent oracle disagrees for 1024");

        if (shortestPath(1).size() != 1 || oracleMinSteps(1) != 0) throw new AssertionError("target=1 boundary failed");
        if (!shortestPath(2).isEmpty() || oracleMinSteps(2) != -1) throw new AssertionError("unreachable boundary failed");
        if (shortestPath(6).size() - 1 != 1 || oracleMinSteps(6) != 1) throw new AssertionError("+5 boundary failed");
        if (shortestPath(18).size() - 1 != 2 || oracleMinSteps(18) != 2) throw new AssertionError("mixed boundary failed");

        int checked = 0;
        for (int target = 1; target <= 3000; target++) {
            List<Step> candidate = shortestPath(target);
            int oracle = oracleMinSteps(target);
            int actual = candidate.isEmpty() ? -1 : candidate.size() - 1;
            if (actual != oracle) throw new AssertionError("oracle mismatch target=" + target + " bfs=" + actual + " oracle=" + oracle);
            if (!candidate.isEmpty()) assertValidPath(target, candidate);
            checked++;
        }
        System.out.println("PASS target=1024 steps=11 deterministic-path=true oracle-targets=" + checked + " target1=true unreachable=true pruning=true");
    }
}
