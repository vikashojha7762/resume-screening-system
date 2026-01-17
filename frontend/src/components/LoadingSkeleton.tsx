import React from 'react';
import { Skeleton, Box, Card, CardContent } from '@mui/material';

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <Box>
      {Array.from({ length: rows }).map((_, index) => (
        <Box key={index} sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Skeleton variant="rectangular" width="100%" height={60} />
        </Box>
      ))}
    </Box>
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="60%" height={32} />
        <Skeleton variant="text" width="40%" height={24} />
        <Skeleton variant="rectangular" width="100%" height={200} sx={{ mt: 2 }} />
      </CardContent>
    </Card>
  );
};

export const DashboardSkeleton: React.FC = () => {
  return (
    <Box>
      <Skeleton variant="text" width={200} height={40} sx={{ mb: 3 }} />
      <Box sx={{ display: 'flex', gap: 2 }}>
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index} sx={{ flex: 1 }}>
            <CardContent>
              <Skeleton variant="circular" width={40} height={40} />
              <Skeleton variant="text" width="60%" height={32} sx={{ mt: 2 }} />
              <Skeleton variant="text" width="40%" height={24} />
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

