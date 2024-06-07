```
                                        
    =*#########*=.                      
  .@#:         @%@*:                    
  =@.          @* =%#-                  
  +@.          @*   -%%-                
  +@.          +@+:...=%%=              
  +@.           .=*******@+             
  +@.                    @*             
  +@.                    -:             
  +@.                 HLS CLONER        
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
This is a simple python script tp download an HLS stream and clone it on your local system. This means, Master manifest file, child manifest files, and all the different bitrates' ts chubks will be copied in the original form.
To use this script run `python3 hls-cloner.py`.
It will ask you for the master manifest url. This script is using multi-threading to download the chunks faster. Enter the threads you want to run. The default value is 5.

In case the above method fails due to complex URL structure of manifest files, use `python3 hls-cloner2.py`.

In case you have requirement to bulk clone many manifest files in 1 go, use `python3 bulk-downloader.py`. You need to provide input.txt file containing all the master manifest files 1 item per new line. The script will download all the files one after another maintaining directory structure. It logs the output in `progress.txt` file in case you want to come back and check for any failures.

### Dependencies:
You need to have `requests` and `m3u8` python packages for running the code. 
Use
`pip3 install requests`
`pip3 install m3u8`


