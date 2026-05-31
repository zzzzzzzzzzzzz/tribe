import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  useDisclosure,
} from "@chakra-ui/react"
import { BsThreeDotsVertical } from "react-icons/bs"
import { FiDownload, FiEdit, FiTrash } from "react-icons/fi"

import {
  type SkillOut,
  SkillsService,
  type TeamOut,
  TeamsService,
  type UploadOut,
  type UserOut,
} from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { downloadJson, safeJsonFilename } from "../../utils/jsonFiles"
import EditUser from "../Admin/EditUser"
import EditSkill from "../Skills/EditSkill"
import EditTeam from "../Teams/EditTeam"
import EditUpload from "../Uploads/EditUpload"
import Delete from "./DeleteAlert"

interface ActionsMenuProps {
  type: string
  value: UserOut | TeamOut | SkillOut | UploadOut
  disabled?: boolean
  readOnly?: boolean
}

const ActionsMenu = ({ type, value, disabled, readOnly }: ActionsMenuProps) => {
  const editUserModal = useDisclosure()
  const deleteModal = useDisclosure()
  const showToast = useCustomToast()

  const resourceName =
    type === "User"
      ? "пользователя"
      : type === "Team"
        ? "команду"
        : type === "Skill"
          ? "навык"
          : "загрузку"

  const canExport = type === "Team" || type === "Skill"

  const handleExport = async () => {
    try {
      if (type === "Team") {
        const team = value as TeamOut
        const teamExport = await TeamsService.exportTeam({ id: team.id })
        downloadJson(teamExport, safeJsonFilename(team.name, "team"))
      } else if (type === "Skill") {
        const skill = value as SkillOut
        const skillExport = await SkillsService.exportSkill({ id: skill.id })
        downloadJson(skillExport, safeJsonFilename(skill.name, "skill"))
      }
    } catch {
      showToast("Не удалось экспортировать JSON.", "", "error")
    }
  }

  return (
    <>
      <Menu>
        <MenuButton
          isDisabled={disabled}
          as={Button}
          rightIcon={<BsThreeDotsVertical />}
          variant="unstyled"
          onClick={(e) => e.stopPropagation()}
        />
        <MenuList>
          {!readOnly && (
            <MenuItem
              onClick={(e) => {
                e.stopPropagation()
                editUserModal.onOpen()
              }}
              icon={<FiEdit fontSize="16px" />}
            >
              Изменить {resourceName}
            </MenuItem>
          )}
          {canExport && (
            <MenuItem
              onClick={(e) => {
                e.stopPropagation()
                void handleExport()
              }}
              icon={<FiDownload fontSize="16px" />}
            >
              Экспорт JSON
            </MenuItem>
          )}
          {!readOnly && (
            <MenuItem
              onClick={(e) => {
                e.stopPropagation()
                deleteModal.onOpen()
              }}
              icon={<FiTrash fontSize="16px" />}
              color="ui.danger"
            >
              Удалить {resourceName}
            </MenuItem>
          )}
        </MenuList>
        {type === "User" ? (
          <EditUser
            user={value as UserOut}
            isOpen={editUserModal.isOpen}
            onClose={editUserModal.onClose}
          />
        ) : type === "Team" ? (
          <EditTeam
            team={value as TeamOut}
            isOpen={editUserModal.isOpen}
            onClose={editUserModal.onClose}
          />
        ) : type === "Skill" ? (
          <EditSkill
            skill={value as SkillOut}
            isOpen={editUserModal.isOpen}
            onClose={editUserModal.onClose}
          />
        ) : (
          <EditUpload
            upload={value as UploadOut}
            isOpen={editUserModal.isOpen}
            onClose={editUserModal.onClose}
          />
        )}
        <Delete
          type={type}
          id={value.id}
          isOpen={deleteModal.isOpen}
          onClose={deleteModal.onClose}
        />
      </Menu>
    </>
  )
}

export default ActionsMenu
