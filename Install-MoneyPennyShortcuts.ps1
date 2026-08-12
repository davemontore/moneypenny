[CmdletBinding()]
param(
    [switch]$RestartExplorer
)

$ErrorActionPreference = "Stop"

$appId = "MoneyPenny.VoiceTyping"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonwPath = Join-Path $projectDir ".venv\Scripts\pythonw.exe"
$scriptPath = Join-Path $projectDir "voice_to_text.py"
$iconPath = Join-Path $projectDir "moneypenny.ico"
$releaseExePath = Join-Path $projectDir "MoneyPenny.exe"
$sourceExePath = Join-Path $projectDir "dist\MoneyPenny\MoneyPenny.exe"
$exePath = if (Test-Path -LiteralPath $releaseExePath) {
    $releaseExePath
}
elseif (Test-Path -LiteralPath $sourceExePath) {
    $sourceExePath
}
else {
    $null
}

$requiredPaths = if ($exePath) {
    @($exePath, $iconPath)
}
else {
    @($pythonwPath, $scriptPath, $iconPath)
}

foreach ($requiredPath in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required MoneyPenny file is missing: $requiredPath"
    }
}

if (-not ("MoneyPenny.WindowsShortcut" -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace MoneyPenny
{
    [ComImport]
    [Guid("00021401-0000-0000-C000-000000000046")]
    internal class ShellLink { }

    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("0000010b-0000-0000-C000-000000000046")]
    internal interface IPersistFile
    {
        [PreserveSig] int GetClassID(out Guid classId);
        [PreserveSig] int IsDirty();
        [PreserveSig] int Load([MarshalAs(UnmanagedType.LPWStr)] string fileName, uint mode);
        [PreserveSig] int Save([MarshalAs(UnmanagedType.LPWStr)] string fileName, [MarshalAs(UnmanagedType.Bool)] bool remember);
        [PreserveSig] int SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string fileName);
        [PreserveSig] int GetCurFile([MarshalAs(UnmanagedType.LPWStr)] out string fileName);
    }

    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    internal struct PropertyKey
    {
        internal Guid FormatId;
        internal uint PropertyId;

        internal PropertyKey(Guid formatId, uint propertyId)
        {
            FormatId = formatId;
            PropertyId = propertyId;
        }
    }

    [StructLayout(LayoutKind.Explicit)]
    internal struct PropVariant
    {
        [FieldOffset(0)] internal ushort VariantType;
        [FieldOffset(8)] internal IntPtr PointerValue;

        internal static PropVariant FromString(string value)
        {
            return new PropVariant
            {
                VariantType = 31,
                PointerValue = Marshal.StringToCoTaskMemUni(value)
            };
        }
    }

    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
    internal interface IPropertyStore
    {
        [PreserveSig] int GetCount(out uint propertyCount);
        [PreserveSig] int GetAt(uint propertyIndex, out PropertyKey key);
        [PreserveSig] int GetValue(ref PropertyKey key, out PropVariant value);
        [PreserveSig] int SetValue(ref PropertyKey key, ref PropVariant value);
        [PreserveSig] int Commit();
    }

    public static class WindowsShortcut
    {
        private const uint ReadWriteMode = 2;
        private const uint ShellChangeAssociated = 0x08000000;

        [DllImport("ole32.dll")]
        private static extern int PropVariantClear(ref PropVariant value);

        [DllImport("shell32.dll")]
        private static extern void SHChangeNotify(uint eventId, uint flags, IntPtr item1, IntPtr item2);

        private static void Check(int result)
        {
            if (result < 0)
                Marshal.ThrowExceptionForHR(result);
        }

        public static void SetAppUserModelId(string shortcutPath, string appId)
        {
            object shellLink = new ShellLink();
            try
            {
                IPersistFile persistFile = (IPersistFile)shellLink;
                Check(persistFile.Load(shortcutPath, ReadWriteMode));

                IPropertyStore propertyStore = (IPropertyStore)shellLink;
                PropertyKey appIdKey = new PropertyKey(
                    new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"),
                    5
                );
                PropVariant appIdValue = PropVariant.FromString(appId);
                try
                {
                    Check(propertyStore.SetValue(ref appIdKey, ref appIdValue));
                    Check(propertyStore.Commit());
                    Check(persistFile.Save(shortcutPath, true));
                }
                finally
                {
                    PropVariantClear(ref appIdValue);
                }
            }
            finally
            {
                if (Marshal.IsComObject(shellLink))
                    Marshal.FinalReleaseComObject(shellLink);
            }
        }

        public static void RefreshShell()
        {
            SHChangeNotify(ShellChangeAssociated, 0, IntPtr.Zero, IntPtr.Zero);
        }
    }
}
'@
}

function New-MoneyPennyShortcut {
    param([Parameter(Mandatory)][string]$ShortcutPath)

    $directory = Split-Path -Parent $ShortcutPath
    New-Item -ItemType Directory -Path $directory -Force | Out-Null

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $null
    try {
        $shortcut = $shell.CreateShortcut($ShortcutPath)
        if ($exePath) {
            $shortcut.TargetPath = $exePath
            $shortcut.Arguments = '--app-dir "' + $projectDir + '"'
        }
        else {
            $shortcut.TargetPath = $pythonwPath
            $shortcut.Arguments = '"' + $scriptPath + '"'
        }
        $shortcut.WorkingDirectory = $projectDir
        $shortcut.Description = "MoneyPenny Voice Typing"
        $shortcut.IconLocation = "$iconPath,0"
        $shortcut.WindowStyle = 7
        $shortcut.Save()
    }
    finally {
        if ($shortcut) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shortcut) }
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell)
    }

    [MoneyPenny.WindowsShortcut]::SetAppUserModelId($ShortcutPath, $appId)
    Write-Host "Installed: $ShortcutPath"
}

$startMenuPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\MoneyPenny.lnk"
$taskbarPath = Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\MoneyPenny.lnk"

New-MoneyPennyShortcut -ShortcutPath $startMenuPath
New-MoneyPennyShortcut -ShortcutPath $taskbarPath
[MoneyPenny.WindowsShortcut]::RefreshShell()

if ($RestartExplorer) {
    Write-Host "Restarting Windows Explorer to refresh the taskbar..."
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
}

Write-Host "MoneyPenny shortcuts now use AppUserModelID $appId and the bundled icon."
