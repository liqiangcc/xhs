#include <limits.h>
#include <stddef.h>
#include <stdio.h>
int main(void) { printf("%zu\n", sizeof(void *) * (size_t)CHAR_BIT); return 0; }
