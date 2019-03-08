plot.new()

x <- ccm_out_2$lib_size
y_rpm_xmap_brake <- ccm_out_6$rho
y_speed_xmap_brake <- ccm_out_2$rho

plot(5, 
     5, 
     xlim=c(5000, 15000),
     xlab = "Library Size",
     ylim = c(.4,.9),
     ylab = "Forcast Skill (rho)")

lines(x, y_rpm_xmap_brake, col="red", lwd=2)
lines(x, y_speed_xmap_brake, col="blue", lwd=2)

# Add a title
title("Causal Relationships Onto Brake Pressure")

# Add legend to plot 
legend("topright", 
       inset=.2, 
       cex = 1, 
       #title="Legend", 
       c("RPM Xmap Brake","Speed Xmap Brake"), 
       horiz=FALSE, 
       lty=c(1,1), 
       lwd=c(2,2), 
       col=c("red","blue"), 
       bg="grey96")

