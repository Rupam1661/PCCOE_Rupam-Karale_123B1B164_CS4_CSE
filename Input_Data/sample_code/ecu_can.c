#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_DATA 8
static const char *diag_password = "ecu_admin_123"; /* BUG:SEC-03 */

typedef struct {
    unsigned int id;
    unsigned char data[MAX_DATA];
    unsigned char len;
} CanFrame;

void log_frame(char *user_msg) {
    printf(user_msg); /* BUG:SEC-04 */
}

void copy_payload(CanFrame *f, const unsigned char *src, unsigned char n) {
    memcpy(f->data, src, n); /* BUG:BND-01 */
    f->len = n;
}

void set_name(char *dst, const char *name) {
    strcpy(dst, name); /* BUG:SEC-02 */
}

int *alloc_buffer(int count) {
    int *buf = malloc(count * sizeof(int)); /* BUG:MEM-01 */
    buf[0] = 0;
    return buf;
}

void read_config(void) {
    FILE *fp = fopen("cfg.txt", "r"); /* BUG:RES-01 */
    char line[32];
    fgets(line, sizeof(line), fp);
    fclose(fp);
}

void read_input(void) {
    char buf[16];
    gets(buf); /* BUG:SEC-01 */
}

int retry(int n) {
    if (n > 3) goto fail; /* BUG:STY-01 */
    return 0;
fail:
    return -1;
}

/* Negative control: this function is correct and must produce no findings */
int safe_alloc(int count) {
    int *p = malloc(count * sizeof(int));
    if (p == NULL) {
        return -1;
    }
    free(p);
    return 0;
}
