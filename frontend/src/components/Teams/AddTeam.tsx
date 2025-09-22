import {
  Button,
  FormControl,
  FormErrorMessage,
  FormHelperText,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Select,
} from "@chakra-ui/react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { useMutation, useQueryClient } from "react-query"

import { type ApiError, type TeamCreate, TeamsService } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"

interface AddTeamProps {
  isOpen: boolean
  onClose: () => void
}

const AddTeam = ({ isOpen, onClose }: AddTeamProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isValid },
  } = useForm<TeamCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
      description: "",
    },
  })

  const addTeam = async (data: TeamCreate) => {
    await TeamsService.createTeam({ requestBody: data })
  }

  const mutation = useMutation(addTeam, {
    onSuccess: () => {
      showToast("Успешно!", "Команда успешно создана.", "success")
      reset()
      onClose()
    },
    onError: (err: ApiError) => {
      const errDetail = err.body?.detail
      showToast("Что-то пошло не так.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries("teams")
    },
  })

  const onSubmit: SubmitHandler<TeamCreate> = (data) => {
    mutation.mutate(data)
  }

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <ModalOverlay />
        <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Добавить команду</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isRequired isInvalid={!!errors.name}>
              <FormLabel htmlFor="name">Название</FormLabel>
              <Input
                id="title"
                {...register("name", {
                  required: "Название обязательно.",
                  pattern: {
                    value: /^[a-zA-Zа-яА-ЯёЁ0-9_\-\s]{1,64}$/,
                    message: "Название может содержать буквы (латиница и кириллица), цифры, пробелы, подчеркивания и дефисы. Макс. длина: 64 символа.",
                  },
                })}
                placeholder="Название"
                type="text"
              />
              {errors.name && (
                <FormErrorMessage>{errors.name.message}</FormErrorMessage>
              )}
            </FormControl>
            <FormControl mt={4}>
              <FormLabel htmlFor="description">Описание</FormLabel>
              <Input
                id="description"
                {...register("description")}
                placeholder="Описание"
                type="text"
              />
            </FormControl>
            <FormControl isRequired mt={4}>
              <FormLabel htmlFor="description">Рабочий процесс</FormLabel>
              <Select
                id="workflow"
                {...register("workflow", { required: true })}
              >
                <option value="hierarchical">Иерархический</option>
                <option value="sequential">Последовательный</option>
              </Select>
              <FormHelperText>
                Вы не сможете изменить рабочий процесс после создания.
              </FormHelperText>
            </FormControl>
          </ModalBody>

          <ModalFooter gap={3}>
            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting}
              isDisabled={!isValid}
            >
              Сохранить
            </Button>
            <Button onClick={onClose}>Отмена</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

export default AddTeam
