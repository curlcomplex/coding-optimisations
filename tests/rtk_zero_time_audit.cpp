// Supplemental audit from the 16 September reviewed coding batch.
// Place one saved implementation's smoother.hpp beside this file (or on -I).
// clang++ -std=c++17 -Wall -Wextra -Werror rtk_zero_time_audit.cpp -o audit
// This was NOT part of the originally frozen worker tests; retain that distinction.
#include "smoother.hpp"
#include <limits>
#include <cmath>
#include <iostream>

int main() {
    ParameterSmoother smoother;
    const double maximum = std::numeric_limits<double>::max();
    smoother.reset(maximum);
    smoother.setTimeMs(0.0);
    smoother.setTarget(-maximum);
    const double result = smoother.process();
    const bool finite = std::isfinite(result);
    const bool snaps = result == -maximum;
    std::cout << "finite=" << finite << " snaps=" << snaps << '\n';
    return finite && snaps ? 0 : 1;
}
