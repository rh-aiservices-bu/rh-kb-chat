import * as React from 'react';
import { Button, Icon, Tooltip } from '@patternfly/react-core';
import { CameraIcon } from '@patternfly/react-icons';

interface CameraButtonProps {
  onClick: () => void;
  isDisabled?: boolean;
}

const CameraButton: React.FunctionComponent<CameraButtonProps> = ({ onClick, isDisabled }) => (
  <Tooltip content="Take a picture" position="top">
    <Button
      variant="plain"
      aria-label="Take a picture"
      isDisabled={isDisabled}
      onClick={onClick}
      icon={<Icon iconSize="xl" isInline><CameraIcon /></Icon>}
    />
  </Tooltip>
);

export default CameraButton;
