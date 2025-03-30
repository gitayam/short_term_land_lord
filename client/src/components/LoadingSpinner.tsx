import React from 'react';
import { Loader, Center } from '@mantine/core';

interface LoadingSpinnerProps {
  fullPage?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

function LoadingSpinner({ fullPage = true, size = 'lg' }: LoadingSpinnerProps) {
  return (
    <Center style={{ width: '100%', height: fullPage ? '100vh' : '100%', minHeight: fullPage ? undefined : '200px' }}>
      <Loader size={size} />
    </Center>
  );
}

export default LoadingSpinner;