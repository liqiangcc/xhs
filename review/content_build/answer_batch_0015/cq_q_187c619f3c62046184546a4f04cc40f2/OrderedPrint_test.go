package orderedprint

import (
	"bytes"
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"
)

func expectedOutput() string {
	var b strings.Builder
	for i := 1; i <= GoroutineCount; i++ {
		fmt.Fprintln(&b, i)
	}
	return b.String()
}

func TestPrintOneToHundredOrdered(t *testing.T) {
	var got bytes.Buffer
	if err := PrintOneToHundred(&got); err != nil {
		t.Fatalf("PrintOneToHundred returned error: %v", err)
	}
	if want := expectedOutput(); got.String() != want {
		t.Fatalf("unexpected output\nwant:\n%s\ngot:\n%s", want, got.String())
	}
}

func TestRepeatedRunsStayOrdered(t *testing.T) {
	want := expectedOutput()
	for run := 0; run < 50; run++ {
		var got bytes.Buffer
		if err := PrintOneToHundred(&got); err != nil {
			t.Fatalf("run %d returned error: %v", run, err)
		}
		if got.String() != want {
			t.Fatalf("run %d violated ordering", run)
		}
	}
}

type failAfterWrites struct {
	remaining int
}

func (w *failAfterWrites) Write(p []byte) (int, error) {
	if w.remaining == 0 {
		return 0, errors.New("synthetic writer failure")
	}
	w.remaining--
	return len(p), nil
}

func TestWriterErrorDoesNotBreakTokenChain(t *testing.T) {
	done := make(chan error, 1)
	go func() {
		done <- PrintOneToHundred(&failAfterWrites{remaining: 10})
	}()

	select {
	case err := <-done:
		if err == nil {
			t.Fatal("expected writer error, got nil")
		}
	case <-time.After(2 * time.Second):
		t.Fatal("PrintOneToHundred deadlocked after writer error")
	}
}

func TestNormalCompletionHasBoundedWait(t *testing.T) {
	done := make(chan error, 1)
	go func() {
		var got bytes.Buffer
		done <- PrintOneToHundred(&got)
	}()

	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("PrintOneToHundred did not complete")
	}
}
