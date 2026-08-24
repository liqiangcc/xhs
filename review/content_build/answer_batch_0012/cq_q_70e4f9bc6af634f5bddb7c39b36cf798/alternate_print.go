package alternateprint

import (
    "fmt"
    "io"
    "sync"
)

// Print1To100 starts two worker goroutines. One prints odd numbers and the other
// prints even numbers. A token passed through channels determines whose turn it is.
func Print1To100(w io.Writer) {
    oddTurn := make(chan struct{}, 1)
    evenTurn := make(chan struct{}, 1)

    var wg sync.WaitGroup
    wg.Add(2)

    go func() {
        defer wg.Done()
        for i := 1; i <= 99; i += 2 {
            <-oddTurn
            fmt.Fprintln(w, i)
            evenTurn <- struct{}{}
        }
    }()

    go func() {
        defer wg.Done()
        for i := 2; i <= 100; i += 2 {
            <-evenTurn
            fmt.Fprintln(w, i)
            if i < 100 {
                oddTurn <- struct{}{}
            }
        }
    }()

    oddTurn <- struct{}{}
    wg.Wait()
}
