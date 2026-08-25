#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include "PointLineDistance.cpp"

static long double oracle(const Point& p, const Point& a, const Point& b) {
    const long double A = b.y - a.y;
    const long double B = a.x - b.x;
    const long double C = -(A * a.x + B * a.y);
    const long double denom = std::hypotl(A, B);
    if (denom == 0.0L) throw std::invalid_argument("degenerate oracle line");
    return std::fabs(A * p.x + B * p.y + C) / denom;
}

static void check(const Point& p, const Point& a, const Point& b, long double expected) {
    const long double actual = pointToLineDistance(p, a, b);
    const long double scale = std::max({1.0L, std::fabs(actual), std::fabs(expected)});
    if (std::fabs(actual - expected) > 1e-15L * scale) throw std::runtime_error("fixed-case mismatch");
    const long double reversed = pointToLineDistance(p, b, a);
    if (std::fabs(actual - reversed) > 1e-15L * scale) throw std::runtime_error("endpoint-order invariance failed");
}

int main() {
    check({1,3}, {0,0}, {4,0}, 3.0L);
    check({5,2}, {2,-10}, {2,20}, 3.0L);
    check({0,1}, {0,0}, {1,1}, std::sqrt(0.5L));
    check({7,7}, {1,1}, {9,9}, 0.0L);
    check({-3,4}, {-1,-2}, {5,10}, oracle({-3,4},{-1,-2},{5,10}));
    bool degenerateThrown = false;
    try { (void)pointToLineDistance({1,2}, {3,4}, {3,4}); }
    catch (const std::invalid_argument&) { degenerateThrown = true; }
    if (!degenerateThrown) throw std::runtime_error("degenerate line must be rejected");

    std::mt19937_64 rng(20260826ULL);
    std::uniform_int_distribution<int> d(-1000, 1000);
    std::uint64_t randomChecked = 0;
    for (int i = 0; i < 5000; ++i) {
        Point a{(long double)d(rng),(long double)d(rng)};
        Point b{(long double)d(rng),(long double)d(rng)};
        if (a.x == b.x && a.y == b.y) { --i; continue; }
        Point p{(long double)d(rng),(long double)d(rng)};
        const long double actual = pointToLineDistance(p,a,b);
        const long double expected = oracle(p,a,b);
        const long double scale = std::max({1.0L,std::fabs(actual),std::fabs(expected)});
        if (std::fabs(actual-expected) > 1e-14L * scale) throw std::runtime_error("random oracle mismatch");
        const long double reversed = pointToLineDistance(p,b,a);
        if (std::fabs(actual-reversed) > 1e-14L * scale) throw std::runtime_error("random endpoint-order mismatch");
        if (actual < 0.0L) throw std::runtime_error("distance must be non-negative");
        ++randomChecked;
    }
    if (randomChecked != 5000) throw std::runtime_error("unexpected random count");
    std::cout << "PASS fixed=5 random=5000 degenerate=rejected order=invariant nonnegative=true\n";
}
