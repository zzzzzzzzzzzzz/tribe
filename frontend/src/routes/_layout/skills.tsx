import {
  Box,
  Container,
  Flex,
  Heading,
  Spinner,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "react-query"
import { type ApiError, SkillsService } from "../../client"
import ActionsMenu from "../../components/Common/ActionsMenu"
import Navbar from "../../components/Common/Navbar"
import useCustomToast from "../../hooks/useCustomToast"

export const Route = createFileRoute("/_layout/skills")({
  component: Skills,
})

function Skills() {
  const showToast = useCustomToast()
  const {
    data: skills,
    isLoading,
    isError,
    error,
  } = useQuery("skills", () => SkillsService.readSkills({}))

  if (isError) {
    const errDetail = (error as ApiError).body?.detail
    showToast("Что-то пошло не так", `${errDetail}`, "error")
  }

  return (
    <>
      {isLoading ? (
        // TODO: Add skeleton
        <Flex justify="center" align="center" height="100vh" width="full">
          <Spinner size="xl" color="ui.main" />
        </Flex>
      ) : (
        skills && (
          <Container maxW="full">
            <Heading
              size="lg"
              textAlign={{ base: "center", md: "left" }}
              pt={12}
            >
              Менеджер навыков
            </Heading>
            <Navbar type={"Skill"} />
            <TableContainer>
              <Table size={{ base: "sm", md: "md" }}>
                <Thead>
                  <Tr>
                    <Th>Имя</Th>
                    <Th>Описание</Th>
                    <Th>Действия</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {skills.data.map((skill) => (
                    <Tr key={skill.id}>
                      <Td maxW="20rem">
                        <Box
                          overflow="hidden"
                          textOverflow="ellipsis"
                          whiteSpace="nowrap"
                        >
                          {skill.name}
                        </Box>
                      </Td>
                      <Td maxW="20rem">
                        <Box
                          overflow="hidden"
                          textOverflow="ellipsis"
                          whiteSpace="nowrap"
                        >
                          {skill.description}
                        </Box>
                      </Td>
                      <Td>
                        <ActionsMenu
                          type={"Skill"}
                          value={skill}
                          readOnly={skill.managed}
                        />
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </TableContainer>
          </Container>
        )
      )}
    </>
  )
}

export default Skills
