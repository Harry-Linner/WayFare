/// 数据同步和离线支持系统
/// 用于处理离线状态、数据同步和冲突解决

import { useAppStore } from '../store/appStore';
import { useEffect, useState, useCallback } from 'react';

export interface SyncState {
  isOnline: boolean;
  pendingSyncs: number;
  lastSyncTime: number | null;
  syncInProgress: boolean;
}

export function useDataSync() {
  const [syncState, setSyncState] = useState<SyncState>({
    isOnline: navigator.onLine,
    pendingSyncs: 0,
    lastSyncTime: null,
    syncInProgress: false,
  });

  const {
    learnerProfile,
    projects,
    documents,
    annotations,
    conversations,
  } = useAppStore();

  // 执行数据同步
  const performSync = useCallback(async () => {
    if (!syncState.isOnline) {
      console.log('⏸️ 离线状态，跳过同步');
      return;
    }

    setSyncState((prev) => ({ ...prev, syncInProgress: true }));

    try {
      console.log('🔄 开始数据同步...');

      // 准备同步数据
      const syncData = {
        learnerProfile: learnerProfile,
        projects,
        documents,
        annotations,
        conversations,
        timestamp: Date.now(),
      };

      // 将数据保存到 localStorage 作为备份
      localStorage.setItem('last-sync-data', JSON.stringify(syncData));

      // 这里可以添加服务器同步逻辑
      // await fetch('/api/sync', { method: 'POST', body: JSON.stringify(syncData) })

      setSyncState((prev) => ({
        ...prev,
        syncInProgress: false,
        lastSyncTime: Date.now(),
        pendingSyncs: 0,
      }));

      console.log('✅ 数据同步完成');
    } catch (error) {
      console.error('❌ 同步失败:', error);
      setSyncState((prev) => ({
        ...prev,
        syncInProgress: false,
        pendingSyncs: (prev.pendingSyncs || 0) + 1,
      }));
    }
  }, [syncState.isOnline, learnerProfile, projects, documents, annotations, conversations]);

  // 监听在线/离线事件
  useEffect(() => {
    const handleOnline = () => {
      console.log('🌐 已连接到网络');
      setSyncState((prev) => ({ ...prev, isOnline: true }));
      performSync();
    };

    const handleOffline = () => {
      console.log('📴 离线模式');
      setSyncState((prev) => ({ ...prev, isOnline: false }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [performSync]);

  // 定期同步（每60秒）
  useEffect(() => {
    const interval = setInterval(() => {
      if (syncState.isOnline) {
        performSync();
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [syncState.isOnline, performSync]);

  return {
    ...syncState,
    performSync,
  };
}

/// 数据冲突解决策略
export const ConflictResolutionStrategy = {
  LOCAL_WINS: 'local_wins' as const,
  REMOTE_WINS: 'remote_wins' as const,
  MERGE: 'merge' as const,
  ASK_USER: 'ask_user' as const,
};

export type ConflictResolutionStrategyType = typeof ConflictResolutionStrategy[keyof typeof ConflictResolutionStrategy];

interface DataVersion<T = unknown> {
  data: T;
  timestamp: number;
  deviceId: string;
}

/**
 * 解决数据冲突
 */
export function resolveConflict<T>(
  local: DataVersion<T>,
  remote: DataVersion<T>,
  strategy: ConflictResolutionStrategyType
): T {
  switch (strategy) {
    case ConflictResolutionStrategy.LOCAL_WINS:
      return local.data;

    case ConflictResolutionStrategy.REMOTE_WINS:
      return remote.data;

    case ConflictResolutionStrategy.MERGE:
      // 简单合并策略：按时间戳合并
      if (typeof local.data === 'object' && typeof remote.data === 'object') {
        return {
          ...local.data,
          ...remote.data,
          _merged: true,
          _local_version: local.timestamp,
          _remote_version: remote.timestamp,
        };
      }
      return local.timestamp > remote.timestamp ? local.data : remote.data;

    case ConflictResolutionStrategy.ASK_USER:
    default:
      console.warn('需要用户确认冲突');
      return local.data; // 默认使用本地数据
  }
}

/**
 * 存储版本控制
 */
export class VersionedStorage {
  private versionKey = 'app-version-history';
  private maxVersions = 10;

  /**
   * 保存数据版本
   */
  public saveVersion<T>(key: string, data: T, deviceId: string = 'local'): void {
    const version: DataVersion = {
      data,
      timestamp: Date.now(),
      deviceId,
    };

    const history = this.getVersionHistory(key);
    history.push(version);

    // 只保留最新的 N 个版本
    if (history.length > this.maxVersions) {
      history.shift();
    }

    localStorage.setItem(
      `${this.versionKey}-${key}`,
      JSON.stringify(history)
    );
  }

  /**
   * 获取版本历史
   */
  public getVersionHistory<T = unknown>(key: string): DataVersion<T>[] {
    const stored = localStorage.getItem(`${this.versionKey}-${key}`);
    return stored ? JSON.parse(stored) : [];
  }

  /**
   * 恢复到特定版本
   */
  public rollbackToVersion<T = unknown>(key: string, versionIndex: number): T | null {
    const history = this.getVersionHistory<T>(key);
    if (versionIndex >= 0 && versionIndex < history.length) {
      return history[versionIndex].data;
    }
    return null;
  }

  /**
   * 获取最新版本
   */
  public getLatestVersion(key: string): DataVersion | null {
    const history = this.getVersionHistory(key);
    return history.length > 0 ? history[history.length - 1] : null;
  }

  /**
   * 清空版本历史
   */
  public clearVersionHistory(key: string) {
    localStorage.removeItem(`${this.versionKey}-${key}`);
  }
}

export const versionedStorage = new VersionedStorage();

/// 使用版本控制保存数据
export function useSyncedState<T>(key: string, initialValue: T) {
  const [state, setState] = useState<T>(() => {
    // 尝试从 localStorage 恢复
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : initialValue;
  });

  const updateState = useCallback(
    (newValue: T | ((prev: T) => T)) => {
      setState((prev) => {
        const updated = typeof newValue === 'function' ? (newValue as (prev: T) => T)(prev) : newValue;

        // 保存到 localStorage
        localStorage.setItem(key, JSON.stringify(updated));

        // 保存版本
        versionedStorage.saveVersion(key, updated);

        return updated;
      });
    },
    [key]
  );

  return [state, updateState] as const;
}
