import { Button, Flex, Icon, Input, useDisclosure } from "@chakra-ui/react"
import { type ChangeEvent, useRef } from "react"
import { FaPlus } from "react-icons/fa"
import { FiUpload } from "react-icons/fi"
import { useQueryClient } from "react-query"

import {
  type SkillExport,
  SkillsService,
  type TeamExport,
  TeamsService,
} from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { readJsonFile } from "../../utils/jsonFiles"
import AddUser from "../Admin/AddUser"
import AddSkill from "../Skills/AddSkill"
import AddTeam from "../Teams/AddTeam"
import AddUpload from "../Uploads/AddUpload"

interface NavbarProps {
  type: string
}

const Navbar = ({ type }: NavbarProps) => {
  const addUserModal = useDisclosure()
  const addTeamModal = useDisclosure()
  const addSkillModal = useDisclosure()
  const addUploadModal = useDisclosure()
  const importInputRef = useRef<HTMLInputElement | null>(null)
  const queryClient = useQueryClient()
  const showToast = useCustomToast()

  const resourceName =
    type === "User"
      ? "пользователя"
      : type === "Team"
        ? "команду"
        : type === "Skill"
          ? "навык"
          : "загрузку"

  const canImport = type === "Team" || type === "Skill"

  const handleImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return

    try {
      if (type === "Team") {
        const teamExport = await readJsonFile<TeamExport>(file)
        await TeamsService.importTeam({ requestBody: teamExport })
        await queryClient.invalidateQueries("teams")
        showToast("Команда импортирована.", "", "success")
      } else if (type === "Skill") {
        const skillExport = await readJsonFile<SkillExport>(file)
        await SkillsService.importSkill({ requestBody: skillExport })
        await queryClient.invalidateQueries("skills")
        showToast("Навык импортирован.", "", "success")
      }
    } catch {
      showToast("Не удалось импортировать JSON.", "", "error")
    }
  }

  return (
    <>
      <Flex py={8} gap={4}>
        {/* TODO: Complete search functionality */}
        {/* <InputGroup w={{ base: '100%', md: 'auto' }}>
                    <InputLeftElement pointerEvents='none'>
                        <Icon as={FaSearch} color='gray.400' />
                    </InputLeftElement>
                    <Input type='text' placeholder='Search' fontSize={{ base: 'sm', md: 'inherit' }} borderRadius='8px' />
                </InputGroup> */}
        <Button
          variant="primary"
          gap={1}
          fontSize={{ base: "sm", md: "inherit" }}
          onClick={
            type === "User"
              ? addUserModal.onOpen
              : type === "Team"
                ? addTeamModal.onOpen
                : type === "Skill"
                  ? addSkillModal.onOpen
                  : addUploadModal.onOpen
          }
        >
          <Icon as={FaPlus} /> Добавить {resourceName}
        </Button>
        {canImport && (
          <>
            <Button
              variant="outline"
              gap={1}
              fontSize={{ base: "sm", md: "inherit" }}
              onClick={() => importInputRef.current?.click()}
            >
              <Icon as={FiUpload} /> Импорт JSON
            </Button>
            <Input
              ref={importInputRef}
              type="file"
              accept="application/json,.json"
              display="none"
              onChange={handleImport}
            />
          </>
        )}
        <AddUser isOpen={addUserModal.isOpen} onClose={addUserModal.onClose} />
        <AddTeam isOpen={addTeamModal.isOpen} onClose={addTeamModal.onClose} />
        <AddSkill
          isOpen={addSkillModal.isOpen}
          onClose={addSkillModal.onClose}
        />
        <AddUpload
          isOpen={addUploadModal.isOpen}
          onClose={addUploadModal.onClose}
        />
      </Flex>
    </>
  )
}

export default Navbar
