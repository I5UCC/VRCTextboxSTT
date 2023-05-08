using System;
using System.Diagnostics;
using System.IO;

namespace TextboxSTT_Launcher
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
                    if (choice.ToLower() == "y")
                    {
                        File.Create(cpu_file);
                        pInfo.Arguments = String.Format("-m pip install -U -r \"{0}\" --no-warn-script-location", currpath + "\\src\\requirements.cpu.txt");
                    }
                    else
                    {
                        pInfo.Arguments = String.Format("-m pip install -U -r \"{0}\" --no-warn-script-location", currpath + "\\src\\requirements.txt");
                    }
                    Process process = Process.Start(pInfo);
                    process.WaitForExit();
                    pInfo.Arguments = "-m pip cache purge";
                    process = Process.Start(pInfo);
                    process.WaitForExit();

                    Console.WriteLine("\nTextboxSTT installed.\n");

                    File.Create(installed_file);
                }
                catch (Exception ex)
                {
                    Console.WriteLine("INSTALLATION FAILED:");
                    Console.WriteLine(ex.Message);
                    Console.ReadLine();
                }
            }

            if (!File.Exists(currpath + "\\config.json"))
            {
                File.Copy(currpath + "\\src\\config.json", currpath + "\\config.json");
            }

            if (first_install)
            {
                Console.Write("Installation Finished. Press Enter to continue...");
            }

            pInfo.WorkingDirectory = currpath + "\\src";
            Console.WriteLine("Starting TextboxSTT...");
            pInfo.FileName = currpath + "\\python\\TextboxSTT.exe";
            pInfo.Arguments = "TextboxSTT.py _ _ _";
            pInfo.UseShellExecute = false;
            Process.Start(pInfo);
        }
    }
}
