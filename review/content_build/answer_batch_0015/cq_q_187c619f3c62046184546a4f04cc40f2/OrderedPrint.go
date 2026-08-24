package orderedprint

import (
	"fmt"
	"io"
)

const GoroutineCount = 100

// PrintOneToHundred starts exactly GoroutineCount workers.
// Worker i waits for its predecessor token, writes i, then hands the token on.
func PrintOneToHundred(w io.Writer) error {
	tokens := make([]chan struct{}, GoroutineCount+1)
	for i := range tokens {
		tokens[i] = make(chan struct{})
	}

	errs := make(chan error, GoroutineCount)

	for i := 1; i <= GoroutineCount; i++ {
		i := i
		go func() {
			<-tokens[i-1]
			_, err := fmt.Fprintln(w, i)
			errs <- err
			tokens[i] <- struct{}{}
		}()
	}

	tokens[0] <- struct{}{}
	<-tokens[GoroutineCount]

	close(errs)
	for err := range errs {
		if err != nil {
			return err
		}
	}
	return nil
}
