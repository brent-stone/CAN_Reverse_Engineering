for (ccm_from in vars) { 
  for (ccm_to in vars[vars != ccm_from]) { 
    cf_temp <- ccf(speed_brake_rpm[, ccm_from], speed_brake_rpm[, ccm_to], type = "correlation", lag.max = 500, plot = FALSE)$acf

    corr_matrix[ccm_from, ccm_to] <- max(abs(cf_temp)) 
  } 
}