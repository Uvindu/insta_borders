I checked in the internet and couldn't find any free/reliable tool to add white borders and watermarks such that the photo will become 1x1 aspect ratio without any changes to the actual image. So I created a python code with Gemini. Might be useful to others, hence posting here.  

Adjustable settings -  
    size_ratio = 0.15            #watermark  
    opacity = 0.6                #watermark  
    color_for_borders = 'white'  
    
    # JPEG QUALITY:  
    # Controls the compression level for saved JPEG files.  
    # 1 is lowest quality, 95 is highest recommended. 100 is nearly lossless.  
    # Higher values result in larger file sizes.  
    jpeg_quality = 95  
"--delete-originals" is optional flags to remove original images   

if you do not want to add watermark just dont provide second file path.  

To run -   
$ python3 img_border_with_watermark.py "/path/to/image/folder" "/path/to/watermark/image" --delete-originals  

original image -    
![image alt](https://github.com/Uvindu/insta_borders/blob/e243f2022977c2c8ffff3eb57f4b16f0baba6529/test.jpg)

processed image -   
![image alt](https://github.com/Uvindu/insta_borders/blob/e243f2022977c2c8ffff3eb57f4b16f0baba6529/test_1x1.jpg)
