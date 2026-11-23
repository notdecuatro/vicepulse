#import <AVFoundation/AVFoundation.h>
#import <Foundation/Foundation.h>
#include <stdio.h>
int main(int argc,char **argv){@autoreleasepool{
for(int i=1;i<argc;i++){
 AVURLAsset *asset=[AVURLAsset URLAssetWithURL:[NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[i]]] options:nil];
 NSArray *v=[asset tracksWithMediaType:AVMediaTypeVideo], *a=[asset tracksWithMediaType:AVMediaTypeAudio];
 printf("%s duration %.3f tracks video=%lu audio=%lu\n",argv[i],CMTimeGetSeconds(asset.duration),(unsigned long)v.count,(unsigned long)a.count);
 if(v.count!=1||a.count!=1)return 1;
 for(AVAssetTrack *t in @[v[0],a[0]]){
 NSError *err=nil;
 AVAssetReader *r=[AVAssetReader assetReaderWithAsset:asset error:&err];
 AVAssetReaderTrackOutput *o=[AVAssetReaderTrackOutput assetReaderTrackOutputWithTrack:t outputSettings:nil];
 [r addOutput:o]; [r startReading]; int n=0; size_t bytes=0; CMSampleBufferRef b;
 while((b=[o copyNextSampleBuffer])){n+=CMSampleBufferGetNumSamples(b);bytes+=CMSampleBufferGetTotalSampleSize(b);CFRelease(b);}
 printf("samples=%d bytes=%zu size=%.0fx%.0f\n",n,bytes,t.naturalSize.width,t.naturalSize.height);
 if(!n||r.status!=AVAssetReaderStatusCompleted)return 2;
 }}return 0;}
}
