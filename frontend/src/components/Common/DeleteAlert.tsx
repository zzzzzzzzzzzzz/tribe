import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  Button,
} from "@chakra-ui/react"
import React from "react"
import { useForm } from "react-hook-form"
import { useMutation, useQueryClient } from "react-query"

import {
  SkillsService,
  TeamsService,
  UploadsService,
  UsersService,
} from "../../client"
import useCustomToast from "../../hooks/useCustomToast"

interface DeleteProps {
  type: string
  id: number
  isOpen: boolean
  onClose: () => void
}

const Delete = ({ type, id, isOpen, onClose }: DeleteProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const cancelRef = React.useRef<HTMLButtonElement | null>(null)
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteEntity = async (id: number) => {
    if (type === "User") {
      await UsersService.deleteUser({ userId: id })
    } else if (type === "Team") {
      await TeamsService.deleteTeam({ id: id })
    } else if (type === "Skill") {
      await SkillsService.deleteSkill({ id: id })
    } else if (type === "Upload") {
      await UploadsService.deleteUpload({ id: id })
    } else {
      throw new Error(`Unexpected type: ${type}`)
    }
  }

  const mutation = useMutation(deleteEntity, {
    onSuccess: () => {
      if (type !== "Upload")
        showToast(
          "Успешно",
          `${type === "User" ? "Пользователь" :
             type === "Team" ? "Команда" :
             type === "Skill" ? "Навык" : "Загрузка"} успешно ${
             type === "User" ? "удален" :
             type === "Team" ? "удалена" :
             type === "Skill" ? "удален" : "удалена"}.`,
          "success",
        )
      onClose()
    },
    onError: () => {
      showToast(
        "Произошла ошибка",
        `Ошибка при удалении ${
          type === "User" ? "пользователя" :
          type === "Team" ? "команды" :
          type === "Skill" ? "навыка" : "загрузки"}.`,
        "error",
      )
    },
    onSettled: () => {
      queryClient.invalidateQueries(
        type === "User"
          ? "users"
          : type === "Team"
            ? "teams"
            : type === "Skill"
              ? "skills"
              : "uploads",
      )
    },
  })

  const onSubmit = async () => {
    mutation.mutate(id)
  }

  return (
    <>
      <AlertDialog
        isOpen={isOpen}
        onClose={onClose}
        leastDestructiveRef={cancelRef}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <AlertDialogOverlay>
          <AlertDialogContent as="form" onSubmit={handleSubmit(onSubmit)}>
            <AlertDialogHeader>
              Удалить {type === "User" ? "пользователя" :
                      type === "Team" ? "команду" :
                      type === "Skill" ? "навык" : "загрузку"}
            </AlertDialogHeader>

            <AlertDialogBody>
              {type === "User" && (
                <span>
                  Все элементы, связанные с этим пользователем, также будут{" "}
                  <strong>безвозвратно удалены. </strong>
                </span>
              )}
              Вы уверены? Это действие нельзя будет отменить.
            </AlertDialogBody>

            <AlertDialogFooter gap={3}>
              <Button
                variant="danger"
                type="submit"
                isLoading={isSubmitting || mutation.isLoading}
              >
                Удалить
              </Button>
              <Button
                ref={cancelRef}
                onClick={onClose}
                isDisabled={isSubmitting}
              >
                Отмена
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </>
  )
}

export default Delete
