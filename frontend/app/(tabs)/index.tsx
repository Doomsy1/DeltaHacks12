import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";

import { useEffect, useRef, useState } from "react";
import {
  Dimensions,
  FlatList,
  ListRenderItemInfo,
  Platform,
  TextStyle,
  View,
  ViewStyle,
  Text,
  Pressable,
  StyleSheet,
  Share,
  ActivityIndicator,
} from "react-native";

import { VideoView, useVideoPlayer } from "expo-video";
import { ReelOverlay } from "../../components/ReelOverlay";
import { Ionicons } from "@expo/vector-icons";
import Config from "../../config";

const { height, width } = Dimensions.get("window");

// Configuration pulled from environment variables
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Function to fetch video list from backend API
async function fetchVideosFromBackend(): Promise<string[]> {
  try {
    const apiUrl = `${API_BASE_URL}/videos/list?limit=4`;
    
    console.log("Fetching 4 videos from backend API:", apiUrl);
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error("Failed to fetch videos from backend:", response.status);
      return [];
    }
    
    const data = await response.json();
    const videos = data.videos || [];
    
    // Extract URLs from the response
    const videoUrls = videos.map((video: any) => video.url);
    
    console.log(`Loaded ${videoUrls.length} videos from backend`);
    return videoUrls;
  } catch (error) {
    console.error("Error fetching videos from backend:", error);
    return [];
  }
}

interface VideoWrapper {
  data: ListRenderItemInfo<string>;
  allVideos: string[];
  visibleIndex: number;
  pause: () => void;
  share: (videoURL: string) => void;
  pauseOverride: boolean;
}

const VideoWrapper = ({
  data,
  allVideos,
  visibleIndex,
  pause,
  pauseOverride,
  share,
}: VideoWrapper) => {
  const bottomHeight = useBottomTabBarHeight();
  const { index, item } = data;

  const player = useVideoPlayer(allVideos[index], (player) => {
    player.loop = true;
    player.muted = false;
  });

  // State for like/dislike
  const [isLiked, setIsLiked] = useState(false);
  const [isDisliked, setIsDisliked] = useState(false);
  const [likeCount, setLikeCount] = useState(12400);
  const [dislikeCount, setDislikeCount] = useState(150);

  const handleLike = () => {
    if (isLiked) {
      setIsLiked(false);
      setLikeCount(likeCount - 1);
    } else {
      setIsLiked(true);
      setLikeCount(likeCount + 1);
      if (isDisliked) {
        setIsDisliked(false);
        setDislikeCount(dislikeCount - 1);
      }
    }
  };

  const handleDislike = () => {
    if (isDisliked) {
      setIsDisliked(false);
      setDislikeCount(dislikeCount - 1);
    } else {
      setIsDisliked(true);
      setDislikeCount(dislikeCount + 1);
      if (isLiked) {
        setIsLiked(false);
        setLikeCount(likeCount - 1);
      }
    }
  };

  // Control playback based on visibility and pause override
  useEffect(() => {
    if (visibleIndex === index && !pauseOverride) {
      player.play();
    } else {
      player.pause();
    }
  }, [visibleIndex, index, pauseOverride, player]);

  // Reset video to 0:00 when scrolling away from it
  useEffect(() => {
    if (visibleIndex !== index) {
      player.currentTime = 0;
    }
  }, [visibleIndex, index, player]);

  return (
    <View
      style={{
        height: Platform.OS === "android" ? height - bottomHeight : height,
        width,
      }}
    >
      <VideoView
        player={player}
        style={{ height: height - bottomHeight, width }}
        contentFit="cover"
        nativeControls={false}
      />

      <Pressable onPress={pause} style={$tapOverlay} />

      <ReelOverlay
        companyName="Company Name"
        title="Video Title Goes Here"
        description="This is a sample description for the video content. It can be up to two lines long."
        likeCount={likeCount}
        dislikeCount={dislikeCount}
        shareCount={3200}
        isLiked={isLiked}
        isDisliked={isDisliked}
        onLike={handleLike}
        onDislike={handleDislike}
        onShare={() => share(item)}
        onProfilePress={() => console.log("Profile pressed")}
      />

      {/* Pause indicator that sticks to this video */}
      {pauseOverride && visibleIndex === index && (
        <View style={$pauseIndicator}>
          <Ionicons name="pause" size={60} color="#fff" style={{ opacity: 0.3 }} />
        </View>
      )}
    </View>
  );
};

export default function HomeScreen() {
  const bottomHeight = useBottomTabBarHeight();

  const [allVideos, setAllVideos] = useState<string[]>([]);
  const [visibleIndex, setVisibleIndex] = useState(0);
  const [pauseOverride, setPauseOverride] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const numOfRefreshes = useRef(0);
  const hasMore = useRef(true);

  // Load initial videos from backend
  useEffect(() => {
    async function loadInitialVideos() {
      try {
        setLoading(true);
        const videos = await fetchVideosFromBackend();
        
        if (videos.length === 0) {
          setError("No videos found");
        } else {
          setAllVideos(videos);
        }
      } catch (err) {
        console.error("Error loading videos:", err);
        setError("Failed to load videos");
      } finally {
        setLoading(false);
      }
    }

    loadInitialVideos();
  }, []);

  const fetchMoreData = async () => {
    // For pagination, you could fetch more videos from Vultr
    // For now, we'll just prevent infinite loading
    if (numOfRefreshes.current > 0) {
      hasMore.current = false;
      return;
    }
    
    numOfRefreshes.current += 1;
    
    // Optionally fetch more videos from Vultr
    // const moreVideos = await fetchVideosFromVultr();
    // setAllVideos([...allVideos, ...moreVideos]);
  };

  const onViewableItemsChanged = (event: any) => {
    const newIndex = Number(event.viewableItems.at(-1).key);
    setVisibleIndex(newIndex);
  };

  const pause = () => {
    setPauseOverride(!pauseOverride);
  };

  const share = (videoURL: string) => {
    setPauseOverride(true);
    setTimeout(() => {
      Share.share({
        title: "Share This Video",
        message: `Check out: ${videoURL}`,
      });
    }, 100);
  };

  // Show loading state
  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: "black", justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#fff" />
        <Text style={{ color: "#fff", marginTop: 20 }}>Loading videos...</Text>
      </View>
    );
  }

  // Show error state
  if (error || allVideos.length === 0) {
    return (
      <View style={{ flex: 1, backgroundColor: "black", justifyContent: "center", alignItems: "center", padding: 20 }}>
        <Ionicons name="cloud-offline" size={60} color="#fff" style={{ opacity: 0.5 }} />
        <Text style={{ color: "#fff", marginTop: 20, fontSize: 18, textAlign: "center" }}>
          {error || "No videos available"}
        </Text>
        <Text style={{ color: "#aaa", marginTop: 10, fontSize: 14, textAlign: "center" }}>
          Make sure your backend is running and Vultr Object Storage is configured
        </Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: "black" }}>
      <FlatList
        pagingEnabled
        snapToInterval={
          Platform.OS === "android" ? height - bottomHeight : undefined
        }
        initialNumToRender={1}
        showsVerticalScrollIndicator={false}
        onViewableItemsChanged={onViewableItemsChanged}
        data={allVideos}
        onEndReachedThreshold={0.3}
        onEndReached={fetchMoreData}
        renderItem={(data) => {
          return (
            <VideoWrapper
              data={data}
              allVideos={allVideos}
              visibleIndex={visibleIndex}
              pause={pause}
              share={share}
              pauseOverride={pauseOverride}
            />
          );
        }}
      />
    </View>
  );
}

const $tapOverlay: ViewStyle = {
  ...StyleSheet.absoluteFillObject,
  backgroundColor: "transparent",
};

const $pauseIndicator: ViewStyle = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: [{ translateX: -30 }, { translateY: -30 }],
  justifyContent: "center",
  alignItems: "center",
  pointerEvents: "none",
};



