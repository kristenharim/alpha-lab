// C++ port of tracks/statarb/bands.py::band_positions — the one path-dependent,
// un-vectorizable hot loop in the statarb backtest. Kept byte-for-byte equivalent
// to the Python branch logic; a parity test enforces exact integer equality.
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <cstdint>

namespace py = pybind11;

// long_floor == NaN means "no floor" (Python's long_floor is None).
static py::array_t<int64_t> band_positions_c(
        py::array_t<double, py::array::c_style | py::array::forcecast> series,
        double entry, double exit_, double long_floor) {
    auto s = series.unchecked<1>();
    const py::ssize_t n = s.shape(0);
    auto out = py::array_t<int64_t>(n);
    auto o = out.mutable_unchecked<1>();
    const bool has_floor = !std::isnan(long_floor);

    int64_t pos = 0;
    for (py::ssize_t i = 0; i < n; ++i) {
        const double v = s(i);
        if (std::isnan(v)) { o(i) = pos; continue; }   // hold through NaN
        const bool too_deep = has_floor && (v < -long_floor);
        if (pos == 0) {
            if (v <= -entry && !too_deep) pos = 1;
            else if (v >= entry)          pos = -1;
        } else if (pos == 1 && too_deep) {              // knife kept falling — stop out
            pos = 0;
        } else if (std::fabs(v) <= exit_) {             // reverted inside exit band
            pos = 0;
        }
        o(i) = pos;
    }
    return out;
}

PYBIND11_MODULE(_fastbands, m) {
    m.doc() = "Fast path-dependent mean-reversion position state machine.";
    m.def("band_positions_c", &band_positions_c,
          py::arg("series"), py::arg("entry"), py::arg("exit_"), py::arg("long_floor"));
}
