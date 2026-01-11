import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  StatusBar,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Colors } from '@/constants/colors';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'expo-router';
import { useApplied } from '@/contexts/AppliedContext';

export default function LikedScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];
  const { user, logout } = useAuth();
  const router = useRouter();
  const { appliedCount } = useApplied();

  const handleLogout = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/login');
          },
        },
      ]
    );
  };

  const isDark = colorScheme === 'dark';

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} />
      
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: isDark ? '#262626' : '#efefef' }]}>
        <Text style={[styles.username, { color: colors.text }]}>
          {user?.email || 'User'}
        </Text>
        <Pressable style={styles.menuButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color={colors.text} />
        </Pressable>
      </View>

      {/* Profile Section */}
      <View style={styles.profileSection}>
        <View style={styles.profileRow}>
          {/* Profile Picture */}
          <View style={styles.profilePicContainer}>
            <View style={styles.profilePic}>
              <Ionicons name="person" size={40} color={colors.text} />
            </View>
          </View>

          {/* Stats */}
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={[styles.statNumber, { color: colors.text }]}>
                {appliedCount}
              </Text>
              <Text style={[styles.statLabel, { color: isDark ? '#a0a0a0' : '#737373' }]}>
                Applied
              </Text>
            </View>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    position: 'relative',
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
  },
  menuButton: {
    position: 'absolute',
    right: 16,
    padding: 4,
  },
  profileSection: {
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profilePicContainer: {
    marginRight: 32,
  },
  profilePic: {
    width: 86,
    height: 86,
    borderRadius: 43,
    backgroundColor: 'rgba(128, 128, 128, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 13,
    fontWeight: '400',
  },
});
