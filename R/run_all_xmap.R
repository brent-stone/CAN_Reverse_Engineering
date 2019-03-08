speed_xmap_rpm <- ccm(speed_brake_rpm, lib_column = "speed", target_column = "rpm", E = 9, lib_sizes = seq(0, 15000, by = 3000), num_samples = 10, random_libs = TRUE, replace = TRUE, num_neighbors = "E+1", tp = 0, silent = TRUE)
save(speed_xmap_rpm, file = "speed_xmap_rpm_v2.Rda")
speed_xmap_brake <- ccm(speed_brake_rpm, lib_column = "speed", target_column = "brake", E = 9, lib_sizes = seq(0, 15000, by = 3000), num_samples = 10, random_libs = TRUE, replace = TRUE, num_neighbors = "E+1", tp = 0, silent = TRUE)
save(speed_xmap_brake, file = "speed_xmap_brake_v2.Rda")

brake_xmap_rpm <- ccm(speed_brake_rpm, lib_column = "brake", target_column = "rpm", E = 9, lib_sizes = seq(0, 15000, by = 3000), num_samples = 10, random_libs = TRUE, replace = TRUE, num_neighbors = "E+1", tp = 0, silent = TRUE)
save(brake_xmap_rpm, file = "brake_xmap_rpm_v2.Rda")
brake_xmap_speed <- ccm(speed_brake_rpm, lib_column = "brake", target_column = "speed", E = 9, lib_sizes = seq(0, 15000, by = 3000), num_samples = 10, random_libs = TRUE, replace = TRUE, num_neighbors = "E+1", tp = 0, silent = TRUE)
save(brake_xmap_speed, file = "brake_xmap_speed_v2.Rda")

rpm_xmap_speed <- ccm(speed_brake_rpm, lib_column = "rpm", target_column = "speed", E = 9, lib_sizes = seq(0, 15000, by = 3000), num_samples = 10, random_libs = TRUE, replace = TRUE, num_neighbors = "E+1", tp = 0,  silent = TRUE)
save(rpm_xmap_speed, file = "rpm_xmap_speed_v2.Rda")
rpm_xmap_brake <- ccm(speed_brake_rpm, lib_column = "rpm", target_column = "brake", E = 9, lib_sizes = seq(0, 15000, by = 3000), num_samples = 10, random_libs = TRUE, replace = TRUE, num_neighbors = "E+1", tp = 0,  silent = TRUE)
save(rpm_xmap_brake, file = "rpm_xmap_brake_v2.Rda")