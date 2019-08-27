To see the original README please go view the project this is forked from, brent-stone/CAN_Reverse_Engineering
 - The vast majority of this project is his work.

This fork of CAN_Reverse_Engineering adds **KnownSignalAnalysis.py**, which takes a single given ARB ID and integrates it.
This given Arb ID is defined in **Main.py** as known_speed_arb_id. This integration is done because the given Arb ID is speed, and the integral of speed is distance.
Therefore, once normalized, the integrated speed signal on the given Arb ID should be extremely similar to the odometer signal.

I will do my best to detail my changes below. In the future the changes will be listed on the commits of the relevant file.

In the function generate_arb_id_dictionary(), located in **PreProcessor.py**, once the known_speed_arb_id is found, it creates a new arb id that is an exact copy.
This exact copy has its' this_id.id set to 256 times the original's, purely because this adds 2 zeroes to the end of the arb id so I wouldn't have to go and mess with the plotting function filenames.

Next, the transform_signal() function located in **KnownSignalAnalysis.py**, which largely shares its code with the function generate_signals() in **LexicalAnalysis.py**.
transform_signal() finds the Arb ID created in generate_arb_id_dictionary() and integrates it's component signals.


During Semantic Analysis, the known integrated speed signal should be clustered with the unknown odometer signal. 

Finally, there are obviously changes in **Main.py**, **Sample.py**, and **Plotter.py** to implement these functions. Specifically there are some new plotting functions to only plot the transformed signal.

I have tested this on 3 vehicles, and it has been successful on 2 of them. The unsuccessful case is likely due to some sort of encoding scheme on the odometer signal.

I am new to using git, and this is my first major python task after 5 years of coding in C, so please excuse if there are any C-isms in my python code or mistakes in the maintenance of the GitHub.
In addition, I mostly focused on throwing this together as fast as possible and there is a huge amount of sloppy coding & technical debt.

I will probably not be maintaining this project moving forward due to the rushed implementation. It's more of a proof of concept. I plan to rewrite this more properly soon.
If you are interested in forking this project or making a pull request, it's probably best if you just wait until the rewrite.

Feel free to email me at jarking@umich.edu with any questions!

 

