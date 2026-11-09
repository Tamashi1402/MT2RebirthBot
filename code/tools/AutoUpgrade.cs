// ============================================================
// AutoUpgrade.cs — Auto-upgrade state check + toggle helper
//
// Compile:  csc AutoUpgrade.cs -r:System.Drawing.dll -r:System.Windows.Forms.dll
//
// Usage:
//   AutoUpgrade.exe status          → prints ACTIVE or INACTIVE, exit 0=active 1=inactive
//   AutoUpgrade.exe enable          → enables if not already active
//   AutoUpgrade.exe disable         → disables if active
//   AutoUpgrade.exe toggle          → toggles regardless of state
//
// HOW TO USE IN MACRO RECORDER:
//   Add "Run Program" step → AutoUpgrade.exe status
//   Then branch on exit code: 0 = lime-green (active), 1 = not active
//
// DETECTION:
//   Scans the bottom-left region for lime-green pixels.
//   Active   = lime-green icon visible (H 80-150°, S≥35%, V≥35%, ≥1% of region)
//   Inactive = all white, grey, or no icon (lime-green below threshold)
//
// TOGGLE KEY:
//   Uses the "=" key (Toggle Auto Upgrade default bind in MT2).
//   Change KEY_CHAR below if your bind is different.
// ============================================================

using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

public class Program
{
    // ── Region to scan for the auto-upgrade icon (bottom-left) ──
    // Adjust x2/y2 if the icon appears outside this box.
    // Currently covers the full bottom-left quadrant of a 1024x576 screen.
    static readonly Rectangle REGION = new Rectangle(0, 390, 320, 186); // x,y,w,h

    // ── Key to press for toggling auto-upgrade (MT2 default: "=") ──
    const string KEY_CHAR = "=";

    // ── Win32 for keypress (SendInput) ──────────────────────────
    const uint INPUT_KEYBOARD   = 1;
    const uint KEYEVENTF_KEYUP  = 0x0002;

    [StructLayout(LayoutKind.Sequential)]
    struct KEYBDINPUT {
        public ushort wVk, wScan;
        public uint dwFlags, time;
        public IntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Explicit)]
    struct INPUT_UNION { [FieldOffset(0)] public KEYBDINPUT ki; }
    [StructLayout(LayoutKind.Sequential)]
    struct INPUT { public uint type; public INPUT_UNION u; }

    [DllImport("user32.dll")]
    static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

    [DllImport("user32.dll")]
    static extern ushort VkKeyScan(char ch);

    // ── Lime-green % match ───────────────────────────────────────
    // Active auto-upgrade shows a lime-green icon/glow in bottom-left.
    // White or absent = inactive.
    // Returns fraction of matching pixels (0.0 – 1.0).
    static float LimeGreenPercent()
    {
        try {
            using (var bmp = new Bitmap(REGION.Width, REGION.Height))
            using (var g = Graphics.FromImage(bmp)) {
                g.CopyFromScreen(
                    new Point(REGION.X, REGION.Y),
                    Point.Empty,
                    REGION.Size
                );

                // Optionally save debug screenshot
                string debugPath = System.IO.Path.Combine(
                    AppDomain.CurrentDomain.BaseDirectory,
                    "debug_crops",
                    DateTime.Now.ToString("HHmmss") + "_autoupgrade_check.png"
                );
                System.IO.Directory.CreateDirectory(
                    System.IO.Path.GetDirectoryName(debugPath)
                );
                bmp.Save(debugPath);

                int match = 0, total = bmp.Width * bmp.Height;
                for (int x = 0; x < bmp.Width; x++)
                for (int y = 0; y < bmp.Height; y++) {
                    Color c = bmp.GetPixel(x, y);
                    float h = c.GetHue();         // 0-360
                    float s = c.GetSaturation();  // 0-1
                    float v = c.GetBrightness();  // 0-1
                    // Lime-green: H 80-150°, S≥35%, V≥35%
                    // Wide tolerances handle day/night tinting
                    if (h >= 80f && h <= 150f && s >= 0.35f && v >= 0.35f)
                        match++;
                }
                return total > 0 ? (float)match / total : 0f;
            }
        }
        catch (Exception ex) {
            Console.Error.WriteLine("[AutoUpgrade] Detection error: " + ex.Message);
            return 0f;
        }
    }

    // Threshold: 1% lime-green = active (wider scan area than auto-strength)
    static bool IsActive() => LimeGreenPercent() >= 0.01f;

    // ── Send the toggle key ──────────────────────────────────────
    static void PressKey()
    {
        ushort vk = (ushort)(VkKeyScan(KEY_CHAR[0]) & 0xFF);
        var inputs = new INPUT[2];
        inputs[0].type = INPUT_KEYBOARD;
        inputs[0].u.ki.wVk = vk;
        inputs[1].type = INPUT_KEYBOARD;
        inputs[1].u.ki.wVk = vk;
        inputs[1].u.ki.dwFlags = KEYEVENTF_KEYUP;
        Thread.Sleep(50);
        SendInput(2, inputs, Marshal.SizeOf(typeof(INPUT)));
        Thread.Sleep(150); // wait for game to register
    }

    // ── Entry point ──────────────────────────────────────────────
    public static void Main(string[] args)
    {
        string cmd = args.Length > 0 ? args[0].ToLower() : "status";
        bool active = IsActive();
        float pct   = LimeGreenPercent();

        switch (cmd) {
            case "status":
                Console.WriteLine(active ? "ACTIVE" : "INACTIVE");
                Console.Error.WriteLine($"[AutoUpgrade] lime-green={pct:P1}  threshold=1%");
                // Exit 0 = active, 1 = inactive
                Environment.Exit(active ? 0 : 1);
                break;

            case "enable":
                if (!active) {
                    Console.WriteLine("[AutoUpgrade] Inactive → pressing key to enable");
                    PressKey();
                    Thread.Sleep(300);
                    Console.WriteLine("[AutoUpgrade] Enabled ✓");
                } else {
                    Console.WriteLine("[AutoUpgrade] Already active — no press needed");
                }
                Environment.Exit(0);
                break;

            case "disable":
                if (active) {
                    Console.WriteLine("[AutoUpgrade] Active → pressing key to disable");
                    PressKey();
                    Thread.Sleep(300);
                    Console.WriteLine("[AutoUpgrade] Disabled ✓");
                } else {
                    Console.WriteLine("[AutoUpgrade] Already inactive — no press needed");
                }
                Environment.Exit(0);
                break;

            case "toggle":
                Console.WriteLine($"[AutoUpgrade] State was {(active ? "ACTIVE" : "INACTIVE")} → toggling");
                PressKey();
                Environment.Exit(0);
                break;

            default:
                Console.Error.WriteLine("Usage: AutoUpgrade.exe [status|enable|disable|toggle]");
                MessageBox.Show(
                    "Usage: AutoUpgrade.exe [status | enable | disable | toggle]",
                    "AutoUpgrade — Usage Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                );
                Environment.Exit(2);
                break;
        }
    }
}
