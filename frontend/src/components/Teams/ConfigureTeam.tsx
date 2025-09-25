import {
  Button,
  Heading,
  IconButton,
  Link,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
  useDisclosure,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "react-query"
import { type ApiError, ApiKeysService } from "../../client"
import { MdOutlineVpnKey } from "react-icons/md"
import AddApiKey from "./AddApiKey"
import { DeleteIcon } from "@chakra-ui/icons"
import useCustomToast from "../../hooks/useCustomToast"

interface ConfigureTeamProps {
  teamId: string
}

export const ConfigureTeam = ({ teamId }: ConfigureTeamProps) => {
  const queryClient = useQueryClient()
  const addApiKeyModal = useDisclosure()
  const showToast = useCustomToast()
  const {
    data: apikeys,
    isLoading,
    isError,
    error,
  } = useQuery("apikeys", () =>
    ApiKeysService.readApiKeys({ teamId: Number.parseInt(teamId) }),
  )

  const deleteApiKey = async (apiKeyId: number) => {
    await ApiKeysService.deleteApiKey({
      teamId: Number.parseInt(teamId),
      id: apiKeyId,
    })
  }

  const deleteApiKeyMutation = useMutation(deleteApiKey, {
    onError: (err: ApiError) => {
      const errDetail = err.body?.detail
      showToast("Не удалось удалить API ключ.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries("apikeys")
    },
    onSuccess: () => {
      showToast("Успешно!", "API ключ успешно удален.", "success")
    },
  })

  const onDeleteHandler = (
    e: React.MouseEvent<HTMLButtonElement>,
    apiKeyId: number,
  ) => {
    e.stopPropagation()
    deleteApiKeyMutation.mutate(apiKeyId)
  }

  if (isError) {
    const errDetail = (error as ApiError).body?.detail
    showToast("Что-то пошло не так.", `${errDetail}`, "error")
  }

  return (
    <VStack spacing={"1rem"} alignItems={"flex-start"}>
      <Heading size="lg">API ключи</Heading>
      <Text>
        API ключи используются для аутентификации при взаимодействии с вашими командами
        через HTTP запросы. Узнайте, как делать запросы из{" "}
        {
          <Link
            href="/redoc#tag/teams/operation/teams-public_stream"
            isExternal
            color="ui.main"
          >
            API документации
          </Link>
        }
        .
      </Text>

      <Button leftIcon={<MdOutlineVpnKey />} onClick={addApiKeyModal.onOpen}>
        Создать API ключ
      </Button>
      <AddApiKey
        teamId={teamId}
        isOpen={addApiKeyModal.isOpen}
        onClose={addApiKeyModal.onClose}
      />
      <Text>
        Вы можете получить доступ к API ключу только при его создании. Если вы
        потеряли ключ, вам нужно будет создать новый. Ваши API ключи перечислены ниже.
      </Text>
      <TableContainer width="100%">
        <Table>
          <Thead>
            <Tr>
              <Th>Описание</Th>
              <Th>API ключ</Th>
              <Th>Создан</Th>
              <Th>Действия</Th>
            </Tr>
          </Thead>
          <Tbody>
            {!isLoading &&
              apikeys?.data.map((apikey) => (
                <Tr key={apikey.id}>
                  <Td maxW="20rem" overflow="hidden" textOverflow="ellipsis">
                    {apikey.description}
                  </Td>
                  <Td>{apikey.short_key}</Td>
                  <Td>{new Date(apikey.created_at).toLocaleString()}</Td>
                  <Td>
                    <IconButton
                      size={"sm"}
                      aria-label="Delete"
                      icon={<DeleteIcon />}
                      onClick={(e) => onDeleteHandler(e, apikey.id)}
                    />
                  </Td>
                </Tr>
              ))}
          </Tbody>
        </Table>
      </TableContainer>
    </VStack>
  )
}

export default ConfigureTeam
