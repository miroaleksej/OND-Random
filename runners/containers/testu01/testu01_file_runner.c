#include <stdio.h>
#include <string.h>
#include "bbattery.h"
#include "ufile.h"
#include "unif01.h"

int main(int argc, char **argv) {
  if (argc < 3) {
    fprintf(stderr, "Usage: %s <battery> <input.bin>\n", argv[0]);
    fprintf(stderr, "Batteries: fips | rabbit | smallcrush | crush | bigcrush\n");
    return 2;
  }

  const char *battery = argv[1];
  const char *path = argv[2];

  unif01_Gen *gen = ufile_CreateReadBin(path, 0);
  if (!gen) {
    fprintf(stderr, "Failed to open input file: %s\n", path);
    return 3;
  }

  if (strcmp(battery, "fips") == 0) {
    bbattery_FIPS(gen);
  } else if (strcmp(battery, "rabbit") == 0) {
    bbattery_Rabbit(gen);
  } else if (strcmp(battery, "smallcrush") == 0) {
    bbattery_SmallCrush(gen);
  } else if (strcmp(battery, "crush") == 0) {
    bbattery_Crush(gen);
  } else if (strcmp(battery, "bigcrush") == 0) {
    bbattery_BigCrush(gen);
  } else {
    fprintf(stderr, "Unknown battery: %s\n", battery);
    ufile_DeleteReadBin(gen);
    return 4;
  }

  ufile_DeleteReadBin(gen);
  return 0;
}
