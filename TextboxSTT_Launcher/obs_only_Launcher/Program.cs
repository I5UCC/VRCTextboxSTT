using System;
using System.Diagnostics;
using System.IO;

namespace obs_only_Launcher
{
    class Program
    {
        static void Main(string[] args)
        {
            string currpath = AppDomain.CurrentDomain.BaseDirectory;
            Directory.SetCurrentDirectory(currpath);
            string installed_file = currpath + "\\python\\INSTALLED";
            string cpu_file = currpath + "\\python\\CPU";
            string python_path = currpath + "\\python\\python.exe";
            string cache_path = currpath + "\\python\\cache";
            string requirements_file_cpu = currpath + "\\src\\requirements.cpu.txt";
            string requirements_file = currpath + "\\src\\requirements.txt";
            bool first_install = false;
            ProcessStartInfo pInfo = new ProcessStartInfo();

            Console.Title = "TextboxSTT Launcher";

            if (!File.Exists(installed_file))
            {
                try
                {
                    first_install = true;
                    Console.WriteLine("NOT INSTALLED YET, STARTING INSTALLER");
                    Console.Write("Install CPU only? [y/N]: ");

                    string choice = Console.ReadLine();
                    pInfo.FileName = python_path;
                    pInfo.WorkingDirectory = currpath;
                    pInfo.UseShellExecute = false;
                    pInfo.EnvironmentVariables.Add("TMPDIR", cache_path);
                    if (choice.ToLower() == "y")
                    {
                        File.Create(cpu_file);
                        pInfo.Arguments = String.Format("-m pip install -U -r \"{0}\" --no-warn-script-location --cache-dir \"{1}\"", requirements_file_cpu, cache_path);
                    }
                    else
                    {
                        pInfo.Arguments = String.Format("-m pip install -U -r \"{0}\" --no-warn-script-location --cache-dir \"{1}\"", requirements_file, cache_path);
                    }
                    Process process = Process.Start(pInfo);
                    process.WaitForExit();
                    pInfo.Arguments = "-m pip cache purge";
                    process = Process.Start(pInfo);
                    process.WaitForExit();

                    Directory.Delete(cache_path, true);
                    Directory.CreateDirectory(cache_path);

                    if (process.ExitCode != 0)
                        throw new Exception("Something unexpectedly went wrong installing TextboxSTT. ExitCode: " + process.ExitCode.ToString());

                    Console.WriteLine("\nTextboxSTT installed.\n");

                    File.Create(installed_file);
                }
                catch (Exception ex)
                {
                    Console.WriteLine("INSTALLATION FAILED:");
                    Console.WriteLine(ex.Message);
                    Console.ReadKey();
                }
            }

            if (!File.Exists(currpath + "\\config.json"))
            {
                File.Copy(currpath + "\\src\\config.json", currpath + "\\config.json");
            }

            if (first_install)
            {
                Console.Write("Installation Finished. Press any key to continue...");
                Console.ReadKey();
            }

            pInfo.WorkingDirectory = currpath + "\\src";
            Console.WriteLine("Starting TextboxSTT obs only mode...");
            pInfo.FileName = currpath + "\\python\\obs_only.exe";
            pInfo.Arguments = "OBSWSTT.py _ _ _";
            pInfo.UseShellExecute = false;
            Process.Start(pInfo);
        }
    }
}
