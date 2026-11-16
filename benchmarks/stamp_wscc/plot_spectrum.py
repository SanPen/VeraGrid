"""Plot the saved full nonlinear EMT Floquet spectrum against STAMP RMS."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src" / "tests" / "data" / "stamp_wscc"
RESULTS = Path(__file__).resolve().parent / "results"
OUTPUT = ROOT / "doc" / "md_source" / "figures" / "dynamics" / "Benchmarking" / "stamp_wscc_nonlinear_emt_spectrum.png"


def main() -> None:
    stamp_data = np.loadtxt(DATA / "stamp_rms_eigenvalues.csv", delimiter=",",
                            skiprows=1, usecols=(1, 2))
    emt_data = np.loadtxt(RESULTS / "nonlinear_emt_floquet_exponents.csv",
                          delimiter=",", skiprows=1)
    stamp = stamp_data[:, 0] + 1j * stamp_data[:, 1]
    emt = emt_data[:, 0] + 1j * emt_data[:, 1]
    omega = 2 * np.pi * 50
    stamp = stamp.real + 1j * ((stamp.imag + omega / 2) % omega - omega / 2)
    assert len(stamp) == 88 and len(emt) == 124

    figure, axes = plt.subplots(1, 2, figsize=(12.8, 5.3), constrained_layout=True)
    for axis in axes:
        axis.scatter(emt.real, emt.imag, marker="o", s=31,
                     facecolors="none", edgecolors="#b2182b", linewidths=1.2,
                     label="Nonlinear EMT Floquet (124 states)")
        axis.scatter(stamp.real, stamp.imag, marker="x", s=38,
                     color="#2166ac", linewidths=1.25,
                     label="STAMP RMS reference (88 states)")
        axis.axvline(0, color="black", linewidth=0.8, linestyle="--")
        axis.axhline(0, color="0.7", linewidth=0.7)
        axis.grid(True, alpha=0.25)
        axis.set_xlabel(r"Real part, $\sigma$ [s$^{-1}$]")
        axis.set_ylabel(r"Imaginary part, $\omega$ [rad/s]")
    axes[0].set_title("Principal Floquet spectrum (visible range)")
    axes[0].set_xlim(-2500, 20)
    axes[0].set_ylim(-170, 170)
    axes[0].legend(loc="lower left")
    axes[1].set_title("Rightmost modes")
    axes[1].set_xlim(-5, 0.25)
    axes[1].set_ylim(-12, 12)
    figure.suptitle("STAMP WSCC: corrected nonlinear EMT and RMS spectra")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, dpi=180)
    plt.close(figure)
    print(OUTPUT)


if __name__ == "__main__":
    main()
