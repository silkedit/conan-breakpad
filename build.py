from conan.packager import ConanMultiPackager

if __name__ == "__main__":
  builder = ConanMultiPackager()
  builder.add_common_builds( pure_c=False )
  filtered_builds = []
  for settings, options, env_vars, build_requires in builder.builds:
    if settings["compiler"] == "apple-clang" or (settings["compiler.version"] == "14" and settings["compiler.runtime"] in ["MD", "MDd"]):
      filtered_builds.append([settings, options, env_vars, build_requires])
  builder.builds = filtered_builds
  builder.run()
