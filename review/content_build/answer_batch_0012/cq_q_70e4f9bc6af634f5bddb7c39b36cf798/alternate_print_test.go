package alternateprint

import (
    "bytes"
    "fmt"
    "strings"
    "testing"
)

func TestPrint1To100(t *testing.T) {
    for run := 0; run < 100; run++ {
        var buf bytes.Buffer
        Print1To100(&buf)

        lines := strings.Fields(buf.String())
        if len(lines) != 100 {
            t.Fatalf("run=%d: want 100 values, got %d: %q", run, len(lines), buf.String())
        }
        for i, got := range lines {
            want := fmt.Sprint(i + 1)
            if got != want {
                t.Fatalf("run=%d index=%d: want %s got %s", run, i, want, got)
            }
        }
    }
}
