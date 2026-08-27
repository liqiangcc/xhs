package main

import (
    "fmt"
    "reflect"
)

func spiralOrder(matrix [][]int) []int {
    if len(matrix) == 0 || len(matrix[0]) == 0 {
        return []int{}
    }

    cols := len(matrix[0])
    for _, row := range matrix {
        if len(row) != cols {
            panic("ragged matrix unsupported")
        }
    }

    top, bottom := 0, len(matrix)-1
    left, right := 0, cols-1
    out := make([]int, 0, len(matrix)*cols)

    for top <= bottom && left <= right {
        for c := left; c <= right; c++ {
            out = append(out, matrix[top][c])
        }
        top++

        for r := top; r <= bottom; r++ {
            out = append(out, matrix[r][right])
        }
        right--

        if top <= bottom {
            for c := right; c >= left; c-- {
                out = append(out, matrix[bottom][c])
            }
            bottom--
        }

        if left <= right {
            for r := bottom; r >= top; r-- {
                out = append(out, matrix[r][left])
            }
            left++
        }
    }

    return out
}

func main() {
    cases := []struct {
        in   [][]int
        want []int
    }{
        {[][]int{}, []int{}},
        {[][]int{{}}, []int{}},
        {[][]int{{1}}, []int{1}},
        {[][]int{{1, 2, 3, 4}}, []int{1, 2, 3, 4}},
        {[][]int{{1}, {2}, {3}, {4}}, []int{1, 2, 3, 4}},
        {[][]int{{1, 2}, {3, 4}, {5, 6}}, []int{1, 2, 4, 6, 5, 3}},
        {[][]int{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}, []int{1, 2, 3, 6, 9, 8, 7, 4, 5}},
        {[][]int{{1, 2, 3, 4}, {5, 6, 7, 8}, {9, 10, 11, 12}}, []int{1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7}},
    }

    for i, tc := range cases {
        got := spiralOrder(tc.in)
        if !reflect.DeepEqual(got, tc.want) {
            panic(fmt.Sprintf("case %d got %v want %v", i, got, tc.want))
        }
    }

    fmt.Println("PASS cases=8 empty/single-row/single-column/rectangular/square no-duplicate-center")
}
