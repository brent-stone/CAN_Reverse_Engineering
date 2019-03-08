for (ccm_from in vars) { 
  for (ccm_to in vars[vars != ccm_from]) { 
    out_temp <- ccm(speed_brake_rpm, E = 9, lib_column = ccm_from, target_column = ccm_to, lib_sizes = n, replace = FALSE, silent = TRUE) 
    ccm_rho_matrix[ccm_from, ccm_to] <- out_temp$rho
  } 
}
