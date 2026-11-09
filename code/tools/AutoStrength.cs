// ============================================================
// AutoStrength.cs — Auto-strength toggle helper for MT2 Rebirth Bot
//
// Compile:   csc AutoStrength.cs -r:System.Drawing.dll -r:System.Windows.Forms.dll
// Usage:     AutoStrength.exe enable
//            AutoStrength.exe disable
//            AutoStrength.exe status
//
// Exit codes: 0 = success / active, 1 = inactive, 2 = usage error
// ============================================================

using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

public class Program
{
    // ── Win32 SendInput ──────────────────────────────────────
    [StructLayout(LayoutKind.Sequential)]
    struct MOUSEINPUT {
        public int  dx, dy;
        public uint mouseData, dwFlags, time;
        public IntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Explicit)]
    struct INPUT_UNION { [FieldOffset(0)] public MOUSEINPUT mi; }
    [StructLayout(LayoutKind.Sequential)]
    struct INPUT { public uint type; public INPUT_UNION u; }

    const uint INPUT_MOUSE            = 0;
    const uint MOUSEEVENTF_MIDDLEDOWN = 0x0020;
    const uint MOUSEEVENTF_MIDDLEUP   = 0x0040;

    [DllImport("user32.dll")]
    static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

    // ── Auto-strength detection region (matches config.py AUTO_STR_REGION) ──
    static readonly Rectangle AUTO_STR_RECT = new Rectangle(855, 447, 167, 43);

    // ── % Tolerance colour check ────────────────────────────
    // Matches Python screen.py logic: checks lime-green pixels with
    // tolerance wide enough to handle day/night tinting.
    // Target: H 80-150°, S ≥ 40%, V ≥ 40%
    // Returns fraction of matching pixels (0.0 – 1.0).
    static float GreenMatchPercent()
    {
        try {
            using (var bmp = new Bitmap(AUTO_STR_RECT.Width, AUTO_STR_RECT.Height))
            using (var g = Graphics.FromImage(bmp)) {
                g.CopyFromScreen(AUTO_STR_RECT.Location, Point.Empty, AUTO_STR_RECT.Size);
                int match = 0, total = bmp.Width * bmp.Height;
                for (int x = 0; x < bmp.Width; x++) {
                    for (int y = 0; y < bmp.Height; y++) {
                        Color c = bmp.GetPixel(x, y);
                        float h = c.GetHue();         // 0-360
                        float s = c.GetSaturation();  // 0-1
                        float v = c.GetBrightness();  // 0-1
                        // Lime-green: H 80-150, S ≥ 0.35, V ≥ 0.35
                        if (h >= 80f && h <= 150f && s >= 0.35f && v >= 0.35f)
                            match++;
                    }
                }
                return total > 0 ? (float)match / total : 0f;
            }
        }
        catch (Exception ex) {
            Console.Error.WriteLine("[AutoStrength] Detection error: " + ex.Message);
            return 0f;
        }
    }

    // Active threshold: 2% of region is lime-green (same as Python)
    static bool IsAutoStrengthActive() => GreenMatchPercent() >= 0.02f;

    // ── Middle-click (toggles auto-strength in-game) ─────────
    static void MiddleClick()
    {
        var inputs = new INPUT[2];
        inputs[0].type = INPUT_MOUSE;
        inputs[0].u.mi.dwFlags = MOUSEEVENTF_MIDDLEDOWN;
        inputs[1].type = INPUT_MOUSE;
        inputs[1].u.mi.dwFlags = MOUSEEVENTF_MIDDLEUP;
        Thread.Sleep(50);
        SendInput(2, inputs, Marshal.SizeOf(typeof(INPUT)));
    }

    // ── Entry point ──────────────────────────────────────────
    public static void Main(string[] args)
    {
        string cmd = args.Length > 0 ? args[0].ToLower() : "status";
        bool active = IsAutoStrengthActive();

        switch (cmd) {
            case "enable":
                if (!active) {
                    Console.WriteLine("[AutoStrength] OFF → clicking ON");
                    MiddleClick();
                    Thread.Sleep(500);
                    Console.WriteLine("[AutoStrength] Enabled ✓");
                } else {
                    Console.WriteLine("[AutoStrength] Already ON");
                }
                Environment.Exit(0);
                break;

            case "disable":
                if (active) {
                    Console.WriteLine("[AutoStrength] ON → clicking OFF");
                    MiddleClick();
                    Thread.Sleep(500);
                    Console.WriteLine("[AutoStrength] Disabled ✓");
                } else {
                    Console.WriteLine("[AutoStrength] Already OFF");
                }
                Environment.Exit(0);
                break;

            case "status":
                Console.WriteLine(active ? "ACTIVE" : "INACTIVE");
                // Exit 0 = active, 1 = inactive (useful for macro branching)
                Environment.Exit(active ? 0 : 1);
                break;

            default:
                Console.Error.WriteLine("Usage: AutoStrength.exe [enable|disable|status]");
                MessageBox.Show(
                    "Usage: AutoStrength.exe [enable | disable | status]",
                    "AutoStrength — Usage Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                );
                Environment.Exit(2);
                break;
        }
    }
}
