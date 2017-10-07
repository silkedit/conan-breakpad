from conans import ConanFile, tools, VisualStudioBuildEnvironment
import os, shutil

class BreakpadConan( ConanFile ):
    name = 'breakpad'
    version = '1.0.0'
    license = 'https://chromium.googlesource.com/breakpad/breakpad/+/master/LICENSE'
    url = 'https://github.com/shinichy/conan-breakpad'
    settings = 'os', 'compiler', 'build_type', 'arch'
    description = "Breakpad is a set of client and server components which implement a crash-reporting system."
    branch = 'chrome_53'
    exports = ["FindBREAKPAD.cmake"]

    def source( self ):
        self.run('git clone https://chromium.googlesource.com/breakpad/breakpad --branch %s --depth 1' % self.branch)

    def build( self ):
        if self.settings.os == 'Macos':
            arch = 'i386' if self.settings.arch == 'x86' else self.settings.arch
            self.run( 'xcodebuild -project breakpad/src/client/mac/Breakpad.xcodeproj -sdk macosx -target Breakpad ARCHS=%s ONLY_ACTIVE_ARCH=YES -configuration %s' % (arch, self.settings.build_type) )
        elif self.settings.os == 'Windows':
            tools.replace_in_file("breakpad/src/build/common.gypi", "'WarnAsError': 'true'", "'WarnAsError': 'false'", strict=True)

            env = {}
            if self.settings.compiler.version == "15":
                env.update({'GYP_MSVS_VERSION': '2017'})
            elif self.settings.compiler.version == "14":
                env.update({'GYP_MSVS_VERSION': '2015'})
            elif self.settings.compiler.version == "12":
                env.update({'GYP_MSVS_VERSION': '2013'})
            elif self.settings.compiler.version == "11":
                env.update({'GYP_MSVS_VERSION': '2012'})
            elif self.settings.compiler.version == "10":
                env.update({'GYP_MSVS_VERSION': '2010'})

            runtimes = {'MT': 0, 'MTd': 1, 'MD': 2, 'MDd': 3}
            runtime_string = "%s" % self.settings.compiler.runtime
            release_runtime = runtimes[runtime_string[:2]]

            env_build = VisualStudioBuildEnvironment(self)
            env.update(env_build.vars)

            with tools.environment_append(env):
                self.run( 'gyp --no-circular-check -D win_release_RuntimeLibrary=%s -D win_debug_RuntimeLibrary=%s breakpad/src/client/windows/breakpad_client.gyp' % (release_runtime, release_runtime+1) )
                vcvars = tools.vcvars_command(self.settings)
                msbuild_cmd = '%s && MSBuild.exe /p:Configuration=%s /p:VisualStudioVersion=%s /p:Platform=%s' % ( vcvars, self.settings.build_type, self.settings.compiler.version, self.settings.arch )
                self.run( '%s breakpad/src/client/windows/common.vcxproj' %  msbuild_cmd)
                self.run( '%s /p:DisableSpecificWarnings="4091;2220" breakpad/src/client/windows/handler/exception_handler.vcxproj' % msbuild_cmd)
                self.run( '%s breakpad/src/client/windows/crash_generation/crash_generation_client.vcxproj' % msbuild_cmd)
                self.run( '%s breakpad/src/client/windows/crash_generation/crash_generation_server.vcxproj' % msbuild_cmd)
                self.run( '%s breakpad/src/client/windows/sender/crash_report_sender.vcxproj' % msbuild_cmd)

    def package( self ):
        self.copy("FindBREAKPAD.cmake", ".", ".")
        self.copy( '*.h', dst='include/common', src='breakpad/src/common' )

        if self.settings.os == 'Macos':
            self.copy( '*.h', dst='include/client/mac', src='breakpad/src/client/mac' )
            # self.copy doesn't preserve symbolic links
            shutil.copytree('breakpad/src/client/mac/build/%s/Breakpad.framework' % self.settings.build_type, os.path.join(self.package_folder, 'lib', 'Breakpad.framework'), symlinks=True)
        elif self.settings.os == 'Windows':
            self.copy( '*.h', dst='include/client/windows', src='breakpad/src/client/windows' )
            self.copy( '*.h', dst='include/google_breakpad', src='breakpad/src/google_breakpad' )
            self.copy( '*.lib', dst='lib', src='breakpad/src/client/windows/%s' % self.settings.build_type, keep_path=False )
            self.copy( '*.lib', dst='lib', src='breakpad/src/client/windows/handler/%s' % self.settings.build_type, keep_path=False )
            self.copy( '*.lib', dst='lib', src='breakpad/src/client/windows/crash_generation/%s' % self.settings.build_type, keep_path=False )
            self.copy( '*.lib', dst='lib', src='breakpad/src/client/windows/sender/%s' % self.settings.build_type, keep_path=False )
            self.copy( '*.exe', dst='bin', src='breakpad/src/tools/windows/binaries' )

    def package_info( self ):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libs = ["common", "crash_generation_client", "crash_generation_server", "crash_report_sender", "exception_handler"]
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
