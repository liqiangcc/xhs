#include <limits.h>
#include <stddef.h>
#include <stdio.h>
const char *classify_pointer_storage_bits(size_t bits) {
    if (bits == 32u) return "32-bit pointer storage";
    if (bits == 64u) return "64-bit pointer storage";
    return "non-32/64 pointer storage";
}
#ifndef XHS_NO_MAIN
int main(void) {
    const size_t bits = sizeof(void *) * (size_t)CHAR_BIT;
    printf("compiled-program pointer storage: %zu bits (%s)\n", bits, classify_pointer_storage_bits(bits));
    return 0;
}
#endif
