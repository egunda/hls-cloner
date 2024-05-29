```
                                        
    =*#########*=.                      
  .@#:         @%@*:                    
  =@.          @* =%#-                  
  +@.          @*   -%%-                
  +@.          +@+:...=%%=              
  +@.           .=*******@+             
  +@.                    @*             
  +@.                    -:             
  +@.                                   
  +@.           :@%%%%%%%%%%%%%%%%%%@=  
  +@.           -@-                .@=  
  +@.           -@-    +%+-        .@=  
  +@.           -@-    *@-*%#=.    .@=  
  +@.           -@-    *@ .=@%=    .@=  
  +@.           -@-    *@#@+:      .@=  
  =@.           -@-    -*:         .@=  
  .@#:          -@-                :@=  
    =*#######:  .####################-  
```

# hls-cloner
This is a simple python script tp download an HLS stream and clone it on your local system.
To use this script run `python3 hls-cloner.py`.
It will ask you for the master manifest url. This script is using multi-threading to download the chunks faster. Enter the threads you want to run. The default value is 5.

### Dependencies:
You need to have `requests` and `m3u8` python packages for running the code. 
Use
`pip3 install requests`
`pip3 install m3u8`


