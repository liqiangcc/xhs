#include <stddef.h>
#include <stdio.h>
#include <string.h>
const char *classify_pointer_storage_bits(size_t bits);
int main(void) {
    if (strcmp(classify_pointer_storage_bits(32u), "32-bit pointer storage") != 0) return 1;
    if (strcmp(classify_pointer_storage_bits(64u), "64-bit pointer storage") != 0) return 2;
    if (strcmp(classify_pointer_storage_bits(48u), "non-32/64 pointer storage") != 0) return 3;
    puts("PASS classify=32,64,other");
    return 0;
}
