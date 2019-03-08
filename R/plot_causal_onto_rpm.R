plot.new()

x <- ccm_out_3$lib_size
y_brake_xmap_rpm <- ccm_out_3$rho
y_speed_xmap_rpm <- ccm_out_1$rho

plot(5, 
     5, 
     xlim=c(5000, 15000),
     xlab = "Library Size",
     ylim = c(.3,1),
     ylab = "Forcast Skill (rho)")

lines(x, y_brake_xmap_rpm, col="red", lwd=2)
lines(x, y_speed_xmap_rpm, col="blue", lwd=2)

# Add a title
title("Causal Relationships Onto Engine RPM")

# Add legend to plot 
legend("topright", 
       inset=.2, 
       cex = 1, 
       #title="Legend", 
       c("Brake Xmap RPM","Speed Xmap RPM"), 
       horiz=FALSE, 
       lty=c(1,1), 
       lwd=c(2,2), 
       col=c("red","blue"), 
       bg="grey96")

