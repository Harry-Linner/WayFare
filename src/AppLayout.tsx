/**
 * 主应用布局管理器
 * 根据应用状态决定展示：入驻流程、项目初始化、主应用
 * 这是整个 WayFare 系统的流量调度层
 */
import { useEffect } from 'react';
import { useAppStore } from './store/appStore';
import { OnboardingFlow } from './components/OnboardingFlow';
import { ProjectSetupWizard } from './components/ProjectSetupWizard';
import { MainApp } from './MainApp.tsx';
import type { LearnerProfile, LearningProject } from './types';

export function AppLayout() {
  const {
    currentUserId,
    learnerProfile,
    setLearnerProfile,
    setCurrentProject,
    addProject,
  } = useAppStore();

  // 步骤 1：检查是否完成入驻
  const needsOnboarding = !learnerProfile;

  // 步骤 2：检查是否完成项目初始化
  const needsProjectSetup = learnerProfile && !useAppStore.getState().currentProjectId;

  useEffect(() => {
    // 初始化：从 localStorage 恢复状态
    const storeState = useAppStore.getState();
    if (learnerProfile && storeState.currentProjectId) {
      // 用户已入驻，重新加载最后的项目
      const lastProject = storeState.projects[storeState.projects.length - 1];
      if (lastProject && currentUserId) {
        setCurrentProject(lastProject.id);
      }
    }
  }, [learnerProfile, currentUserId, setCurrentProject]);

  // ============ Flow 1: 入驻流程 ============
  if (needsOnboarding) {
    return (
      <div className="flex items-center justify-center h-screen bg-white">
        <div className="w-full max-w-2xl mx-auto">
          <OnboardingFlow
            onComplete={(profile: LearnerProfile) => {
              setLearnerProfile(profile);
            }}
          />
        </div>
      </div>
    );
  }

  // ============ Flow 2: 项目初始化 ============
  if (needsProjectSetup) {
    return (
      <div className="flex items-center justify-center h-screen bg-white">
        <div className="w-full max-w-2xl mx-auto">
          <ProjectSetupWizard
            onComplete={(project: LearningProject) => {
              addProject(project);
              setCurrentProject(project.id);
            }}
          />
        </div>
      </div>
    );
  }

  // ============ Flow 3: 主应用 ============
  return <MainApp />;
}
