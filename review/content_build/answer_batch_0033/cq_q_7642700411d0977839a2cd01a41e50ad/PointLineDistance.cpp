#include <cmath>
#include <stdexcept>

struct Point {
    long double x;
    long double y;
};

long double pointToLineDistance(const Point& p, const Point& a, const Point& b) {
    const long double dx = b.x - a.x;
    const long double dy = b.y - a.y;
    const long double length = std::hypotl(dx, dy);
    if (length == 0.0L) {
        throw std::invalid_argument("line requires two distinct points");
    }

    const long double wx = p.x - a.x;
    const long double wy = p.y - a.y;
    const long double twiceArea = dx * wy - dy * wx;
    return std::fabs(twiceArea) / length;
}
