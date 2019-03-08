plot.new()

x <- ccm_out_4$lib_size
y_brake_xmap_speed <- ccm_out_4$rho
y_rpm_xmap_speed <- ccm_out_5$rho

plot(5, 
     5, 
     xlim=c(5000, 15000),
     xlab = "Library Size",
     ylim = c(.6,.9),
     ylab = "Forcast Skill (rho)")

lines(x, y_brake_xmap_speed, col="red", lwd=2)
lines(x, y_rpm_xmap_speed, col="blue", lwd=2)

# Add a title
title("Causal Relationships Onto Speed")

# Add legend to plot 
legend("topright", 
       inset=.1, 
       cex = 1, 
       #title="Legend", 
       c("Brake Xmap Speed","RPM Xmap Speed"), 
       horiz=FALSE, 
       lty=c(1,1), 
       lwd=c(2,2), 
       col=c("red","blue"), 
       bg="grey96")

