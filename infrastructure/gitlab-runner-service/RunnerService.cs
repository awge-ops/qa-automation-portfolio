using System;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Net.Http;
using System.ServiceProcess;
using System.Threading.Tasks;
using System.Timers;

namespace GitLabRunnerService
{
    /// <summary>
    /// Windows Service that bootstraps, registers, and manages a GitLab Runner.
    ///
    /// On start: reads token → writes config.toml → registers runner → starts runner process.
    /// On stop: kills runner processes → unregisters runner.
    /// </summary>
    public partial class RunnerService : ServiceBase
    {
        private const string BasePath = @"C:\GitLab-Runner";
        private const string GitLabUrl = "https://gitlab.example.com/";
        private const string RunnerDescription = "windows-runner-01";
        private const string RunnerExecutor = "shell";
        private const string RunnerShell = "pwsh";
        private const string RunnerBinaryUrl =
            "https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-windows-amd64.exe";

        private int _runnerProcessId;
        private int _registerProcessId;
        private string _token;

        public RunnerService()
        {
            InitializeComponent();
        }

        protected override void OnStart(string[] args)
        {
            EnsureBaseDirectory();

            _token = File.ReadAllText(Path.Combine(BasePath, "token.txt")).Trim();
            WriteConfig(_token);

            RegisterRunner();
            StartRunner();

            Task.Run(() => DownloadLatestBinaryAsync("gitlab-runner.exe"));
        }

        protected override void OnStop()
        {
            KillProcessTree(_runnerProcessId);
            KillProcessTree(_registerProcessId);
            UnregisterRunner();
        }

        private void EnsureBaseDirectory()
        {
            if (!Directory.Exists(BasePath))
                Directory.CreateDirectory(BasePath);
        }

        private void WriteConfig(string token)
        {
            string config =
                $"concurrent = 1\r\n" +
                $"check_interval = 0\r\n" +
                $"connection_max_age = \"15m0s\"\r\n" +
                $"shutdown_timeout = 0\r\n\r\n" +
                $"[session_server]\r\n" +
                $"  session_timeout = 1800\r\n\r\n" +
                $"[[runners]]\r\n" +
                $"  name = \"{RunnerDescription}\"\r\n" +
                $"  url = \"{GitLabUrl}\"\r\n" +
                $"  token = \"{token}\"\r\n" +
                $"  executor = \"{RunnerExecutor}\"\r\n" +
                $"  shell = \"{RunnerShell}\"\r\n" +
                $"  [runners.cache]\r\n" +
                $"    MaxUploadedArchiveSize = 0\r\n";

            string configPath = Path.Combine(BasePath, "config.toml");
            File.WriteAllText(configPath, config);
        }

        private void RegisterRunner()
        {
            var process = CreateHiddenProcess(
                Path.Combine(BasePath, "gitlab-runner.exe"),
                $"register --url=\"{GitLabUrl}\" --registration-token=\"{_token}\" " +
                $"--description=\"{RunnerDescription}\" --executor=\"{RunnerExecutor}\" --non-interactive"
            );
            process.Start();
            _registerProcessId = process.Id;
        }

        private void StartRunner()
        {
            var process = CreateHiddenProcess(
                Path.Combine(BasePath, "gitlab-runner.exe"),
                $"run --config \"{Path.Combine(BasePath, "config.toml")}\""
            );
            process.Start();
            _runnerProcessId = process.Id;
        }

        private void UnregisterRunner()
        {
            var process = CreateHiddenProcess(
                Path.Combine(BasePath, "gitlab-runner.exe"),
                $"unregister --token=\"{_token}\""
            );
            process.Start();
        }

        private static Process CreateHiddenProcess(string fileName, string arguments)
        {
            return new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = fileName,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                }
            };
        }

        private static void KillProcessTree(int pid)
        {
            if (pid == 0) return;

            using var searcher = new ManagementObjectSearcher(
                $"Select * From Win32_Process Where ParentProcessID={pid}");

            foreach (ManagementObject child in searcher.Get())
            {
                KillProcessTree(Convert.ToInt32(child["ProcessID"]));
            }

            try
            {
                Process.GetProcessById(pid).Kill();
            }
            catch (ArgumentException)
            {
                // Process already exited
            }
        }

        private static async Task DownloadLatestBinaryAsync(string fileName)
        {
            string destination = Path.Combine(BasePath, fileName);
            using var client = new HttpClient();
            using var response = await client.GetAsync(RunnerBinaryUrl);
            response.EnsureSuccessStatusCode();
            using var fs = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None);
            await response.Content.CopyToAsync(fs);
        }
    }
}
